from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId


def build_transcription_document(
    user_id: str,
    text: str,
    file_name: str,
    file_size: int,
    r2_key: str,
    duration_seconds: Optional[float] = None,
) -> dict:
    document = {
        "user_id": ObjectId(user_id),
        "text": text,
        "file_name": file_name,
        "file_size": file_size,
        "r2_key": r2_key,
        "duration_seconds": duration_seconds,
        "created_at": datetime.now(timezone.utc),
    }
    return document
