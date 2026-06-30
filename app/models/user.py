from datetime import datetime, timezone
from typing import Optional


def build_user_document(
    email: str,
    password_hash: Optional[str] = None,
    google_id: Optional[str] = None,
    terms_accepted_at: Optional[datetime] = None,
) -> dict:
    user = {
        "email": email,
        "password_hash": password_hash,
        "google_id": google_id,
        "plan": "free",
        "created_at": datetime.now(timezone.utc),
        "terms_accepted_at": terms_accepted_at,
    }
    return user
