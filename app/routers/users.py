from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_user, get_user_repository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserOut
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)) -> UserOut:
    user_out = UserOut(
        id=str(current_user["_id"]),
        email=current_user["email"],
        plan=current_user["plan"],
        created_at=current_user["created_at"],
        terms_accepted=current_user.get("terms_accepted_at") is not None,
    )
    return user_out


@router.post("/me/accept-terms", status_code=status.HTTP_204_NO_CONTENT)
async def accept_terms(
    current_user: dict = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
) -> None:
    await user_service.accept_terms(str(current_user["_id"]), user_repo)
