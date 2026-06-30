from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status

from app.logger import logger
from app.repositories.llm_usage_repository import LlmUsageRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.stt_usage_repository import SttUsageRepository
from app.repositories.transcription_repository import TranscriptionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth import verify_access_token
from app.services.mongo import get_db


def get_user_repository() -> UserRepository:
    database = get_db()
    repository = UserRepository(database)
    return repository


def get_transcription_repository() -> TranscriptionRepository:
    database = get_db()
    repository = TranscriptionRepository(database)
    return repository


def get_llm_usage_repository() -> LlmUsageRepository:
    database = get_db()
    repository = LlmUsageRepository(database)
    return repository


def get_stt_usage_repository() -> SttUsageRepository:
    database = get_db()
    repository = SttUsageRepository(database)
    return repository


def get_review_repository() -> ReviewRepository:
    database = get_db()
    return ReviewRepository(database)


async def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict:
    # Vérifier que le cookie est présent
    if access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
        )

    # Déléguer la logique métier au service — dependencies.py ne fait que traduire en HTTPException
    try:
        user = await verify_access_token(token=access_token, user_repo=user_repo)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )

    logger.info(f"Utilisateur authentifié : {user['email']}")
    return user
