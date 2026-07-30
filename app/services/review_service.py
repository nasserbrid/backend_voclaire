from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewOut


class AlreadyReviewed(Exception):
    pass


def _doc_to_out(doc: dict) -> ReviewOut:
    return ReviewOut(
        id=str(doc["_id"]),
        first_name=doc["first_name"],
        company=doc["company"],
        content=doc["content"],
        rating=doc["rating"],
        plan=doc["plan"],
        created_at=doc["created_at"],
    )


async def submit(
    user: dict,
    first_name: str,
    company: str,
    content: str,
    rating: int,
    review_repo: ReviewRepository,
) -> ReviewOut:
    user_id = str(user["_id"])
    existing = await review_repo.find_by_user_id(user_id)
    if existing:
        raise AlreadyReviewed()
    plan = user.get("plan", "free")
    document = await review_repo.create(
        user_id=user_id,
        first_name=first_name,
        company=company,
        plan=plan,
        content=content,
        rating=rating,
    )
    return _doc_to_out(document)


async def list_public(review_repo: ReviewRepository) -> list[ReviewOut]:
    documents = await review_repo.get_visible()
    return [_doc_to_out(doc) for doc in documents]
