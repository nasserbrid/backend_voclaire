from app.logger import logger
from app.repositories.contact_repository import ContactRepository
from app.services.email_service import send_contact_notification


async def submit(
    user: dict,
    subject: str,
    message: str,
    contact_repo: ContactRepository,
) -> dict:
    user_id = str(user["_id"])
    email = user["email"]
    plan = user.get("plan", "free")

    contact = await contact_repo.create(
        user_id=user_id,
        email=email,
        subject=subject,
        message=message,
    )

    try:
        await send_contact_notification(
            from_email=email,
            from_plan=plan,
            subject=subject,
            message=message,
        )
    except Exception as exc:
        logger.error(f"[contact] Échec envoi email notification : {exc}")

    return contact
