"""FastAPI routes for conversations."""

import json
import os
import sys

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

sys.path.insert(0, os.path.dirname(__file__))
from export_utils import build_content_disposition, format_export_markdown, sanitize_filename
from models import ActionRequest, ArtifactResponse, ConversationResponse, StartRequest, StepsResponse, StepModel
from orchestrator import Orchestrator
from redis_store import RedisStore

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

store = RedisStore()
orchestrator = Orchestrator(store)


@router.post("")
def create_conversation():
    conv_id = store.create_conversation()
    return {"id": conv_id}


@router.get("/{conv_id}")
def get_conversation(conv_id: str):
    data = store.get_conversation(conv_id)
    if not data:
        raise HTTPException(404, "Conversation not found")
    return ConversationResponse(
        id=data.get("id", conv_id),
        status=data.get("status", "created"),
        topic=data.get("topic", ""),
        requirements=data.get("requirements", ""),
        mode=data.get("mode", ""),
        category=data.get("category", ""),
    )


@router.post("/{conv_id}/start")
def start_conversation(conv_id: str, req: StartRequest):
    data = store.get_conversation(conv_id)
    if not data:
        raise HTTPException(404, "Conversation not found")
    if data.get("status") == "running":
        raise HTTPException(400, "Conversation already running")
    orchestrator.start_workflow(conv_id, req.topic, req.requirements, req.mode, req.category)
    return {"status": "started"}


@router.get("/{conv_id}/steps")
def get_steps(conv_id: str):
    if not store.get_conversation(conv_id):
        raise HTTPException(404, "Conversation not found")
    steps = store.get_steps(conv_id)
    return StepsResponse(steps=[StepModel(**s) for s in steps])


def _format_artifact(content: str) -> ArtifactResponse:
    fmt = "markdown"
    if content.strip().startswith("{"):
        try:
            parsed = json.loads(content)
            if isinstance(parsed.get("result"), str):
                content = parsed["result"]
            elif isinstance(parsed, dict):
                content = json.dumps(parsed, ensure_ascii=False, indent=2)
                fmt = "json"
        except json.JSONDecodeError:
            pass
    return ArtifactResponse(content=content, format=fmt)


@router.get("/{conv_id}/artifacts/{step_id}")
def get_artifact(conv_id: str, step_id: str):
    content = store.get_artifact(conv_id, step_id)
    if content is None:
        raise HTTPException(404, "Artifact not found")
    return _format_artifact(content)


@router.post("/{conv_id}/actions")
def submit_action(conv_id: str, req: ActionRequest):
    if not store.get_conversation(conv_id):
        raise HTTPException(404, "Conversation not found")
    orchestrator.submit_action(conv_id, req.step_id, req.action, req.payload)
    return {"status": "ok"}


@router.get("/{conv_id}/export")
def export_article(conv_id: str):
    data = store.get_conversation(conv_id)
    if not data:
        raise HTTPException(404, "Conversation not found")
    content = format_export_markdown(data)
    if not content:
        raise HTTPException(400, "No export available yet")
    title = data.get("article_title") or data.get("topic") or "article"
    return PlainTextResponse(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": build_content_disposition(sanitize_filename(title))},
    )
