from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.common import MongoModel, utc_now


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class Conversation(MongoModel):
    user_id: str
    activity_id: int | None = None
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
