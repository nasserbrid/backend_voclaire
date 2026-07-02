from unittest.mock import AsyncMock, MagicMock

from app.services import payment_service


async def test_activate_pro_sets_plan_and_customer_id():
    user_repo = MagicMock()
    user_repo.set_plan = AsyncMock()
    user_repo.set_stripe_customer_id = AsyncMock()

    await payment_service.activate_pro(
        user_id="user_id_123",
        customer_id="cus_stripe_abc",
        user_repo=user_repo,
    )

    user_repo.set_plan.assert_awaited_once_with("user_id_123", "pro")
    user_repo.set_stripe_customer_id.assert_awaited_once_with("user_id_123", "cus_stripe_abc")


async def test_deactivate_pro_reverts_plan_to_free():
    user_repo = MagicMock()
    user_repo.find_by_stripe_customer_id = AsyncMock(
        return_value={"_id": "user_id_123"}
    )
    user_repo.set_plan = AsyncMock()

    await payment_service.deactivate_pro(
        customer_id="cus_stripe_abc",
        user_repo=user_repo,
    )

    user_repo.set_plan.assert_awaited_once_with("user_id_123", "free")


async def test_deactivate_pro_noop_when_customer_not_found():
    user_repo = MagicMock()
    user_repo.find_by_stripe_customer_id = AsyncMock(return_value=None)
    user_repo.set_plan = AsyncMock()

    await payment_service.deactivate_pro(
        customer_id="cus_inconnu",
        user_repo=user_repo,
    )

    user_repo.set_plan.assert_not_called()
