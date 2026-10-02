from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.auth import Language, Level, ScriptPref


class DocumentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    filename: str
    file_type: str
    file_size: int
    page_count: int | None
    chunk_count: int
    status: str
    error: str | None
    created_at: datetime
    updated_at: datetime | None


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=6000)


class DocumentChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)   # this session's earlier turns
    language: Language = "en"
    level: Level = "beginner"
    script: ScriptPref = "auto"


class AllDocumentsChatIn(DocumentChatIn):
    document_ids: list[int] | None = Field(default=None, max_length=100)   # None = every ready document
