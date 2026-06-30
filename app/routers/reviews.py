from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_review_repository
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewOut
from app.services import review_service
from app.services.review_service import AlreadyReviewed

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
async def post_review(
    body: ReviewCreate,
    current_user: dict = Depends(get_current_user),
    review_repo: ReviewRepository = Depends(get_review_repository),
) -> ReviewOut:
    try:
        review = await review_service.submit(
            user=current_user,
            content=body.content,
            rating=body.rating,
            review_repo=review_repo,
        )
    except AlreadyReviewed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vous avez déjà laissé un avis.",
        )
    return ReviewOut(
        id=str(review["_id"]),
        author_name=review["author_name"],
        content=review["content"],
        rating=review["rating"],
        plan=review["plan"],
        created_at=review["created_at"],
    )


@router.get("", response_model=list[ReviewOut])
async def get_reviews(
    review_repo: ReviewRepository = Depends(get_review_repository),
) -> list[ReviewOut]:
    reviews = await review_service.list_public(review_repo=review_repo)
    return [
        ReviewOut(
            id=str(r["_id"]),
            author_name=r["author_name"],
            content=r["content"],
            rating=r["rating"],
            plan=r.get("plan", "free"),
            created_at=r["created_at"],
        )
        for r in reviews
    ]
