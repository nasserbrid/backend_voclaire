from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TranscriptionOut(BaseModel):
    id: str
    text: str
    improved_text: Optional[str] = None
    structured_content: Optional[dict] = None
    file_name: str
    file_size: int
    duration_seconds: Optional[float]
    created_at: datetime


class ImproveRequest(BaseModel):
    mode: str  # "correction" | "reformulation" | "résumé" | "structured_meeting"
