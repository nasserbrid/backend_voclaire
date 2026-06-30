from app.repositories.review_repository import ReviewRepository


class AlreadyReviewed(Exception):
    pass


async def submit(
    user: dict,
    content: str,
    rating: int,
    review_repo: ReviewRepository,
) -> dict:
    user_id = str(user["_id"])
    existing = await review_repo.find_by_user_id(user_id)
    if existing:
        raise AlreadyReviewed()
    author_name = user["email"].split("@")[0]
    plan = user.get("plan", "free")
    return await review_repo.create(
        user_id=user_id,
        author_name=author_name,
        plan=plan,
        content=content,
        rating=rating,
    )


async def list_public(review_repo: ReviewRepository) -> list[dict]:
    return await review_repo.get_visible()
