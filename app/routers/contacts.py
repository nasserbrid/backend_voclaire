from fastapi import APIRouter, Depends, Request, status

from app.dependencies import get_contact_repository, get_current_user
from app.limiter import limiter
from app.repositories.contact_repository import ContactRepository
from app.schemas.contact import ContactIn, ContactOut
from app.services import contact_service

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def submit_contact(
    request: Request,
    body: ContactIn,
    current_user: dict = Depends(get_current_user),
    contact_repo: ContactRepository = Depends(get_contact_repository),
) -> ContactOut:
    result = await contact_service.submit(
        user=current_user,
        subject=body.subject,
        message=body.message,
        contact_repo=contact_repo,
    )
    return ContactOut(
        id=result["id"],
        user_id=result["user_id"],
        email=result["email"],
        subject=result["subject"],
        message=result["message"],
        created_at=result["created_at"],
    )
