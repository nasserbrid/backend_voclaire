from datetime import datetime, timezone

from app.logger import logger
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import capture
from app.services.auth import hash_password, verify_password
from app.services.email_service import send_welcome_email


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
    capture(str(user_id), "signup", {"plan": "free"})
    try:
        await send_welcome_email(email)
    except Exception:
        logger.warning(f"Échec envoi email de bienvenue à {email}")
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


async def get_or_create_google_user(
    google_id: str,
    email: str,
    user_repo: UserRepository,
) -> dict:
    user_by_google_id = await user_repo.find_by_google_id(google_id)
    if user_by_google_id is not None:
        logger.info(f"Connexion Google (compte Google connu) : {email}")
        return {"user_id": str(user_by_google_id["_id"]), "plan": user_by_google_id["plan"]}

    user_by_email = await user_repo.find_by_email(email)
    if user_by_email is not None:
        user_id = str(user_by_email["_id"])
        await user_repo.link_google_id(user_id=user_id, google_id=google_id)
        logger.info(f"Liaison Google sur compte existant : {email}")
        return {"user_id": user_id, "plan": user_by_email["plan"]}

    user_id = await user_repo.create(email=email, password_hash=None, google_id=google_id)
    logger.info(f"Inscription via Google (nouveau compte) : {email}")
    capture(str(user_id), "signup", {"plan": "free"})
    try:
        await send_welcome_email(email)
    except Exception:
        logger.warning(f"Échec envoi email de bienvenue (Google) à {email}")
    return {"user_id": user_id, "plan": "free"}
