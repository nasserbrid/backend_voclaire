from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
