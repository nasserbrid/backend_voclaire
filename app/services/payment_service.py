from app.logger import logger
from app.repositories.user_repository import UserRepository
from app.services.analytics_service import capture


async def activate_pro(user_id: str, customer_id: str, user_repo: UserRepository) -> None:
    await user_repo.set_plan(user_id, "pro")
    await user_repo.set_stripe_customer_id(user_id, customer_id)
    logger.info(f"Plan pro activé pour user {user_id}")
    capture(str(user_id), "upgrade", {})


async def deactivate_pro(customer_id: str, user_repo: UserRepository) -> None:
    user = await user_repo.find_by_stripe_customer_id(customer_id)
    if user is not None:
        user_id = str(user["_id"])
        await user_repo.set_plan(user_id, "free")
        logger.info(f"Plan repassé free pour user {user_id}")
