from datetime import datetime
from enum import Enum

from pydantic import Field

from app.models.common import MongoModel, utc_now


class LlmLogStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class LlmLog(MongoModel):
    request_id: str
    user_id: str
    conversation_id: str | None = None
    activity_ids: list[int] = Field(default_factory=list)
    provider_name: str
    model_name: str
    prompt_version: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int
    status: LlmLogStatus
    error_code: str | None = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
