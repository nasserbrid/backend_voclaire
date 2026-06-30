from datetime import datetime, timezone

from bson import ObjectId


def build_review_document(
    user_id: str,
    author_name: str,
    plan: str,
    content: str,
    rating: int,
) -> dict:
    return {
        "user_id": ObjectId(user_id),
        "author_name": author_name,
        "plan": plan,
        "content": content,
        "rating": rating,
        "is_visible": True,
        "created_at": datetime.now(timezone.utc),
    }
