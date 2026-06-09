"""Redis storage for conversation state."""

import json
import time
import uuid
from typing import Any, Dict, List, Optional

import redis


CONVERSATION_TTL = 7 * 24 * 3600


class RedisStore:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def create_conversation(self) -> str:
        conv_id = str(uuid.uuid4())
        key = f"conversation:{conv_id}"
        self.client.hset(key, mapping={
            "id": conv_id,
            "status": "created",
            "created_at": str(time.time()),
        })
        self.client.expire(key, CONVERSATION_TTL)
        return conv_id

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, str]]:
        data = self.client.hgetall(f"conversation:{conv_id}")
        return data or None

    def update_conversation(self, conv_id: str, **fields):
        key = f"conversation:{conv_id}"
        if fields:
            self.client.hset(key, mapping={k: str(v) for k, v in fields.items()})
        self.client.expire(key, CONVERSATION_TTL)

    def add_step(self, conv_id: str, step: Dict[str, Any]):
        key = f"conversation:{conv_id}:steps"
        self.client.rpush(key, json.dumps(step, ensure_ascii=False))
        self.client.expire(key, CONVERSATION_TTL)

    def get_steps(self, conv_id: str) -> List[Dict[str, Any]]:
        raw = self.client.lrange(f"conversation:{conv_id}:steps", 0, -1)
        return [json.loads(s) for s in raw]

    def update_step(self, conv_id: str, step_id: str, **fields):
        steps = self.get_steps(conv_id)
        for i, step in enumerate(steps):
            if step["step_id"] == step_id:
                step.update(fields)
                self.client.lset(
                    f"conversation:{conv_id}:steps", i,
                    json.dumps(step, ensure_ascii=False),
                )
                return step
        return None

    def save_artifact(self, conv_id: str, step_id: str, content: str):
        key = f"conversation:{conv_id}:artifacts:{step_id}"
        self.client.set(key, content, ex=CONVERSATION_TTL)

    def get_artifact(self, conv_id: str, step_id: str) -> Optional[str]:
        return self.client.get(f"conversation:{conv_id}:artifacts:{step_id}")

    def publish_event(self, conv_id: str, event: Dict[str, Any]):
        channel = f"conversation:{conv_id}:events"
        self.client.publish(channel, json.dumps(event, ensure_ascii=False))

    def push_task(self, payload: Dict[str, Any], queue: str = "tasks:default"):
        if "id" not in payload:
            payload["id"] = str(uuid.uuid4())
        payload["timestamp"] = int(time.time())
        self.client.rpush(queue, json.dumps(payload, ensure_ascii=False))
        return payload["id"]

    def wait_task(self, task_id: str, timeout: int = 600) -> Optional[Dict[str, Any]]:
        import time as _time
        start = _time.time()
        while _time.time() - start < timeout:
            state = self.client.hgetall(f"task:{task_id}:state")
            if state:
                status = state.get("status")
                if status == "completed":
                    result_raw = state.get("result")
                    if result_raw:
                        try:
                            return json.loads(result_raw)
                        except json.JSONDecodeError:
                            return {"result": result_raw}
                    return {}
                if status == "failed":
                    raise RuntimeError(state.get("error") or state.get("extra_info") or "Task failed")
            _time.sleep(1)
        raise TimeoutError(f"Task {task_id} timed out")
