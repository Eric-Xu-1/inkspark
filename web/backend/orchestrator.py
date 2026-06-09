"""Workflow orchestrator — replaces produce_task.py CLI logic."""

import json
import logging
import re
import threading
import time
import uuid
from typing import Any, Dict, Optional

from redis_store import RedisStore

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "research": "小美",
    "outline": "小青",
    "section": "小青",
    "review": "小尹",
}


class Orchestrator:
    def __init__(self, store: RedisStore):
        self.store = store
        self._locks: Dict[str, threading.Lock] = {}
        self._pending: Dict[str, threading.Event] = {}
        self._actions: Dict[str, Dict[str, Any]] = {}

    def _lock(self, conv_id: str) -> threading.Lock:
        if conv_id not in self._locks:
            self._locks[conv_id] = threading.Lock()
        return self._locks[conv_id]

    def _emit(self, conv_id: str, event_type: str, data: Optional[Dict] = None):
        event = {"type": event_type, "timestamp": time.time()}
        if data:
            event.update(data)
        self.store.publish_event(conv_id, event)

    def _new_step(self, phase: str, title: str, status: str = "pending", detail: str = "") -> Dict:
        return {
            "step_id": str(uuid.uuid4()),
            "phase": phase,
            "title": title,
            "status": status,
            "agent": AGENT_MAP.get(phase, ""),
            "detail": detail,
            "artifact_key": None,
            "created_at": time.time(),
        }

    def _add_step(self, conv_id: str, step: Dict) -> Dict:
        self.store.add_step(conv_id, step)
        self._emit(conv_id, "step_update", {"step": step})
        return step

    def _update_step(self, conv_id: str, step_id: str, **fields) -> Optional[Dict]:
        step = self.store.update_step(conv_id, step_id, **fields)
        if step:
            self._emit(conv_id, "step_update", {"step": step})
        return step

    def _normalize_section_content(
        self, content: str, section_index: int, section_title: str,
    ) -> str:
        """Strip duplicate headings that LLM may still emit."""
        text = content.strip()
        if not text:
            return text

        title_escaped = re.escape(section_title.strip())
        patterns = [
            rf"^#{{1,6}}\s*第\s*{section_index}\s*节[：:\s]*{title_escaped}\s*\n+",
            rf"^#{{1,6}}\s*第\s*{section_index}\s*节[^\n]*\n+",
            rf"^#{{1,6}}\s*{title_escaped}\s*\n+",
            r"^#{1,6}\s+.+\n+",
        ]
        for pattern in patterns:
            new_text = re.sub(pattern, "", text, count=1, flags=re.MULTILINE)
            if new_text != text:
                text = new_text.strip()
                break

        return text

    def _normalize_artifact(self, content: Any) -> str:
        if isinstance(content, dict):
            inner = content.get("result")
            if isinstance(inner, str):
                return inner
            return json.dumps(content, ensure_ascii=False, indent=2)
        if content is None:
            return ""
        return str(content)

    def _save_artifact(self, conv_id: str, step_id: str, content: Any):
        self.store.save_artifact(conv_id, step_id, self._normalize_artifact(content))

    def _wait_user(self, conv_id: str, step_id: str, timeout: int = 3600) -> Dict[str, Any]:
        key = f"{conv_id}:{step_id}"
        event = threading.Event()
        self._pending[key] = event
        self._emit(conv_id, "awaiting_user", {"step_id": step_id})
        if not event.wait(timeout):
            raise TimeoutError("等待用户操作超时")
        action = self._actions.pop(key, {"action": "cancel"})
        self._pending.pop(key, None)
        return action

    def submit_action(self, conv_id: str, step_id: str, action: str, payload: Optional[Dict] = None):
        key = f"{conv_id}:{step_id}"
        self._actions[key] = {"action": action, "payload": payload or {}}
        ev = self._pending.get(key)
        if ev:
            ev.set()

    def start_workflow(self, conv_id: str, topic: str, requirements: str, mode: str, category: str):
        def run():
            try:
                self._run(conv_id, topic, requirements, mode, category)
            except Exception as e:
                logger.exception("Workflow failed")
                self.store.update_conversation(conv_id, status="failed", error=str(e))
                self._emit(conv_id, "error", {"message": str(e)})

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def _submit_and_wait(self, conv_id: str, payload: Dict) -> Dict:
        task_id = self.store.push_task(payload)
        return self.store.wait_task(task_id)

    def _run(self, conv_id: str, topic: str, requirements: str, mode: str, category: str):
        self.store.update_conversation(
            conv_id, status="running", topic=topic, requirements=requirements,
            mode=mode, category=category,
        )

        # --- Research phase ---
        s1 = self._add_step(conv_id, self._new_step("research", "发起调研请求", "completed", topic[:40]))
        s2 = self._add_step(conv_id, self._new_step("research", "深度调研搜索", "running", "正在全网搜索..."))
        try:
            result = self._submit_and_wait(conv_id, {
                "type": "article_generation",
                "phase": "research",
                "topic": topic,
                "requirements": f"{requirements} [模式:{mode}] [类型:{category}]",
            })
            research_text = result.get("result", "")
        except Exception as e:
            self._update_step(conv_id, s2["step_id"], status="failed", detail=str(e))
            raise

        self._update_step(conv_id, s2["step_id"], status="completed", detail="调研完成")
        s3 = self._add_step(conv_id, self._new_step("research", "调研成果汇报", "awaiting_user", "请确认写作角度"))
        self._save_artifact(conv_id, s3["step_id"], research_text)
        s3 = self._update_step(conv_id, s3["step_id"], artifact_key=s3["step_id"]) or s3
        self._emit(conv_id, "step_completed", {"step": s3})

        action = self._wait_user(conv_id, s3["step_id"])
        if action["action"] == "cancel":
            self.store.update_conversation(conv_id, status="cancelled")
            return
        chosen = action.get("payload", {}).get("chosen_direction") or research_text.split("\n")[0]
        if action["action"] == "revise":
            feedback = action.get("payload", {}).get("feedback", "")
            requirements = f"{requirements} (修改: {feedback})"
        self._update_step(conv_id, s3["step_id"], status="completed")
        self.store.update_conversation(conv_id, chosen_direction=chosen)

        # --- Outline phase ---
        outline_step = self._add_step(conv_id, self._new_step("outline", "生成文章大纲", "running"))
        try:
            outline_result = self._submit_and_wait(conv_id, {
                "type": "article_generation",
                "phase": "outline",
                "topic": topic,
                "requirements": requirements,
                "chosen_direction": chosen,
            })
        except Exception as e:
            self._update_step(conv_id, outline_step["step_id"], status="failed", detail=str(e))
            raise

        outline_data = outline_result.get("result")
        if isinstance(outline_data, str):
            outline_md = outline_data
            sections = []
            article_title = chosen
        else:
            sections = outline_data.get("sections") or outline_data.get("chapters") or []
            article_title = outline_data.get("title") or outline_data.get("course_title") or chosen
            outline_md = f"# {article_title}\n\n"
            for i, sec in enumerate(sections):
                outline_md += f"## 第{i+1}节 {sec['title']}\n{sec.get('summary','')}\n\n"

        self._save_artifact(conv_id, outline_step["step_id"], outline_md)
        outline_step = self._update_step(
            conv_id, outline_step["step_id"], status="awaiting_user",
            artifact_key=outline_step["step_id"], detail=f"{len(sections)} 个章节",
        ) or outline_step
        self._emit(conv_id, "step_completed", {"step": outline_step})

        while True:
            action = self._wait_user(conv_id, outline_step["step_id"])
            if action["action"] == "cancel":
                self.store.update_conversation(conv_id, status="cancelled")
                return
            if action["action"] == "confirm":
                self._update_step(conv_id, outline_step["step_id"], status="completed")
                break
            feedback = action.get("payload", {}).get("feedback", "")
            requirements = f"{requirements} (大纲修改: {feedback})"
            self._update_step(conv_id, outline_step["step_id"], status="running", detail="重新生成大纲...")
            outline_result = self._submit_and_wait(conv_id, {
                "type": "article_generation", "phase": "outline",
                "topic": topic, "requirements": requirements, "chosen_direction": chosen,
            })
            outline_data = outline_result.get("result")
            if isinstance(outline_data, dict):
                sections = outline_data.get("sections") or outline_data.get("chapters") or []
                article_title = outline_data.get("title") or article_title
                outline_md = f"# {article_title}\n\n"
                for i, sec in enumerate(sections):
                    outline_md += f"## 第{i+1}节 {sec['title']}\n{sec.get('summary','')}\n\n"
            self._save_artifact(conv_id, outline_step["step_id"], outline_md)
            self._update_step(conv_id, outline_step["step_id"], status="awaiting_user",
                              detail=f"{len(sections)} 个章节")

        if not sections:
            sections = [{"title": "正文", "summary": chosen}]

        self.store.update_conversation(conv_id, article_title=article_title)
        article_parts = [f"# {article_title}\n"]

        # --- Section phase ---
        for i, sec in enumerate(sections):
            sec_step = self._add_step(
                conv_id,
                self._new_step("section", f"撰写第{i+1}节：{sec['title']}", "running"),
            )
            sec_reqs = requirements
            while True:
                try:
                    sec_result = self._submit_and_wait(conv_id, {
                        "type": "article_generation",
                        "phase": "section",
                        "topic": topic,
                        "requirements": sec_reqs,
                        "section_index": i + 1,
                        "section_title": sec["title"],
                        "section_summary": sec.get("summary", ""),
                        "article_title": article_title,
                    })
                except Exception as e:
                    self._update_step(conv_id, sec_step["step_id"], status="failed", detail=str(e))
                    raise

                content = self._normalize_section_content(
                    sec_result.get("result", ""), i + 1, sec["title"],
                )
                self._save_artifact(conv_id, sec_step["step_id"], content)
                sec_step = self._update_step(
                    conv_id, sec_step["step_id"], status="awaiting_user",
                    artifact_key=sec_step["step_id"],
                ) or sec_step
                self._emit(conv_id, "step_completed", {"step": sec_step})

                action = self._wait_user(conv_id, sec_step["step_id"])
                if action["action"] == "cancel":
                    self.store.update_conversation(conv_id, status="cancelled")
                    return
                if action["action"] == "confirm":
                    self._update_step(conv_id, sec_step["step_id"], status="completed")
                    article_parts.append(f"\n## 第{i+1}节 {sec['title']}\n\n{content}")
                    break
                feedback = action.get("payload", {}).get("feedback", "")
                sec_reqs = f"{sec_reqs} (修改: {feedback})"
                self._update_step(conv_id, sec_step["step_id"], status="running", detail="重新撰写...")

        full_article = "\n".join(article_parts)
        self.store.update_conversation(conv_id, full_article=full_article)

        # --- Review phase ---
        review_step = self._add_step(conv_id, self._new_step("review", "审核润色报告", "running"))
        try:
            review_result = self._submit_and_wait(conv_id, {
                "type": "article_generation",
                "phase": "review",
                "topic": topic,
                "requirements": requirements,
                "chosen_direction": chosen,
                "article_title": article_title,
                "article_content": full_article,
            })
            review_text = review_result.get("result", "")
        except Exception as e:
            self._update_step(conv_id, review_step["step_id"], status="failed", detail=str(e))
            raise

        review_artifact = f"# 审核报告\n\n{review_text.strip()}"
        export_content = f"{full_article.strip()}\n\n---\n\n{review_artifact}"
        self._save_artifact(conv_id, review_step["step_id"], review_artifact)
        review_step = self._update_step(
            conv_id, review_step["step_id"], status="awaiting_user",
            artifact_key=review_step["step_id"],
        ) or review_step
        self._emit(conv_id, "step_completed", {"step": review_step})

        action = self._wait_user(conv_id, review_step["step_id"])
        if action["action"] != "cancel":
            self._update_step(conv_id, review_step["step_id"], status="completed")
            self.store.update_conversation(conv_id, status="done", export=export_content)
            self._emit(conv_id, "conversation_done", {"step_id": review_step["step_id"]})
