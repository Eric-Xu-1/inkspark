"""Pydantic models for InkSpark Web API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StartRequest(BaseModel):
    topic: str
    requirements: str = ""
    mode: str = "启发模式 (预览版)"
    category: str = "技术文章"
    search_scope: Dict[str, bool] = Field(default_factory=lambda: {
        "notes": False,
        "knowledge_base": False,
        "web": True,
        "literature": True,
    })


class ActionRequest(BaseModel):
    action: str  # confirm | revise | cancel
    step_id: str
    payload: Optional[Dict[str, Any]] = None


class StepModel(BaseModel):
    step_id: str
    phase: str
    title: str
    status: str
    agent: str = ""
    detail: str = ""
    artifact_key: Optional[str] = None
    created_at: float = 0


class ConversationResponse(BaseModel):
    id: str
    status: str
    topic: str = ""
    requirements: str = ""
    mode: str = ""
    category: str = ""


class StepsResponse(BaseModel):
    steps: List[StepModel]


class ArtifactResponse(BaseModel):
    content: str
    format: str = "markdown"
