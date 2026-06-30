from datetime import datetime, timezone

from app.logger import logger
from app.repositories.user_repository import UserRepository
from app.services.auth import hash_password, verify_password


class EmailAlreadyTaken(Exception):
    pass


class InvalidCredentials(Exception):
    pass


async def register(email: str, password: str, user_repo: UserRepository) -> dict:
    existing_user = await user_repo.find_by_email(email)
    if existing_user is not None:
        raise EmailAlreadyTaken()

    password_hash = hash_password(password)
    terms_accepted_at = datetime.now(timezone.utc)
    user_id = await user_repo.create(email=email, password_hash=password_hash, terms_accepted_at=terms_accepted_at)
    logger.info(f"Inscription : {email}")
    return {"user_id": user_id, "plan": "free"}


async def accept_terms(user_id: str, user_repo: UserRepository) -> None:
    await user_repo.set_terms_accepted(user_id)


async def login(email: str, password: str, user_repo: UserRepository) -> dict:
    user = await user_repo.find_by_email(email)
    password_is_valid = user is not None and verify_password(password, user["password_hash"])
    if not password_is_valid:
        raise InvalidCredentials()

    logger.info(f"Connexion : {email}")
    return {"user_id": str(user["_id"]), "plan": user["plan"]}
