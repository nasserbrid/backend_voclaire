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
        return await review_service.submit(
            user=current_user,
            first_name=body.first_name,
            company=body.company,
            content=body.content,
            rating=body.rating,
            review_repo=review_repo,
        )
    except AlreadyReviewed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vous avez déjà laissé un avis.",
        )


@router.get("", response_model=list[ReviewOut])
async def get_reviews(
    review_repo: ReviewRepository = Depends(get_review_repository),
) -> list[ReviewOut]:
    return await review_service.list_public(review_repo=review_repo)
