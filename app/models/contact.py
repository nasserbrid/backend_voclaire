from datetime import datetime, timezone


def build_contact_document(
    user_id: str,
    email: str,
    subject: str,
    message: str,
) -> dict:
    return {
        "user_id": user_id,
        "email": email,
        "subject": subject,
        "message": message,
        "created_at": datetime.now(timezone.utc),
    }
