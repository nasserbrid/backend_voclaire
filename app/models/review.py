from datetime import datetime, timezone

from bson import ObjectId


def build_review_document(
    user_id: str,
    first_name: str,
    company: str,
    plan: str,
    content: str,
    rating: int,
) -> dict:
    return {
        "user_id": ObjectId(user_id),
        "first_name": first_name,
        "company": company,
        "plan": plan,
        "content": content,
        "rating": rating,
        "is_visible": False,
        "created_at": datetime.now(timezone.utc),
    }
