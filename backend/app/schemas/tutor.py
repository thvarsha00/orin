from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.auth import Language, Level, ScriptPref


class TutorChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None
    language: Language = "en"
    level: Level = "beginner"
    script: ScriptPref = "auto"


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    has_image: bool = False   # the file itself is fetched from /api/tutor/messages/{id}/image


class ConversationOut(BaseModel):
    id: int
    title: str
    language: str
    level: str
    created_at: datetime
