from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TranscriptionOut(BaseModel):
    id: str
    status: str = "done"
    text: Optional[str] = None
    improved_text: Optional[str] = None
    structured_content: Optional[dict] = None
    segments: Optional[list] = None
    file_name: str
    file_size: int
    duration_seconds: Optional[float]
    created_at: datetime


class ImproveRequest(BaseModel):
    mode: str  # "correction" | "reformulation" | "résumé" | "structured_meeting"


class PresignRequest(BaseModel):
    file_name: str
    content_type: str


class PresignResponse(BaseModel):
    upload_url: str
    r2_key: str


class ConfirmRequest(BaseModel):
    r2_key: str
    file_name: str
    content_type: str
    file_size: int
    duration_seconds: float
    source: Literal["file", "recording"]
    num_speakers: Optional[int] = Field(None, ge=1, le=20)
