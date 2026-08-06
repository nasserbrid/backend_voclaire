from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import user_service
from app.services.user_service import EmailAlreadyTaken, EmailNotVerified, InvalidCredentials


async def test_register_ok():
    user_repo = MagicMock()
    user_repo.find_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value="user_id_abc")

    with patch("app.services.user_service.hash_password", return_value="hashed_pw"), \
         patch("app.services.user_service.send_welcome_email", new_callable=AsyncMock), \
         patch("app.services.user_service.capture"):
        result = await user_service.register(
            email="nouveau@example.com",
            password="motdepasse",
            user_repo=user_repo,
        )

    assert result == {"user_id": "user_id_abc", "plan": "free"}
    user_repo.find_by_email.assert_awaited_once_with("nouveau@example.com")
    user_repo.create.assert_awaited_once()


async def test_register_sends_welcome_email():
    user_repo = MagicMock()
    user_repo.find_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value="user_id_abc")

    with patch("app.services.user_service.hash_password", return_value="hashed_pw"), \
         patch("app.services.user_service.send_welcome_email", new_callable=AsyncMock) as mock_welcome, \
         patch("app.services.user_service.capture"):
        await user_service.register(
            email="nouveau@example.com",
            password="motdepasse",
            user_repo=user_repo,
        )

    mock_welcome.assert_awaited_once_with("nouveau@example.com")


async def test_google_new_user_sends_welcome_email():
    user_repo = MagicMock()
    user_repo.find_by_google_id = AsyncMock(return_value=None)
    user_repo.find_by_email = AsyncMock(return_value=None)
    user_repo.create = AsyncMock(return_value="new_google_user_id")

    with patch("app.services.user_service.send_welcome_email", new_callable=AsyncMock) as mock_welcome, \
         patch("app.services.user_service.capture"):
        result = await user_service.get_or_create_google_user(
            google_id="google123",
            email="google@example.com",
            email_verified=True,
            user_repo=user_repo,
        )

    assert result == {"user_id": "new_google_user_id", "plan": "free"}
    mock_welcome.assert_awaited_once_with("google@example.com")


async def test_google_existing_user_no_welcome_email():
    existing_user = {"_id": "existing_id", "plan": "pro"}
    user_repo = MagicMock()
    user_repo.find_by_google_id = AsyncMock(return_value=existing_user)

    with patch("app.services.user_service.send_welcome_email", new_callable=AsyncMock) as mock_welcome:
        result = await user_service.get_or_create_google_user(
            google_id="google123",
            email="existing@example.com",
            email_verified=True,
            user_repo=user_repo,
        )

    assert result == {"user_id": "existing_id", "plan": "pro"}
    mock_welcome.assert_not_awaited()


async def test_google_login_rejects_unverified_email():
    user_repo = MagicMock()
    user_repo.find_by_google_id = AsyncMock()
    user_repo.find_by_email = AsyncMock()
    user_repo.link_google_id = AsyncMock()

    with pytest.raises(EmailNotVerified):
        await user_service.get_or_create_google_user(
            google_id="google123",
            email="non-verifie@example.com",
            email_verified=False,
            user_repo=user_repo,
        )

    user_repo.find_by_email.assert_not_awaited()
    user_repo.link_google_id.assert_not_awaited()


async def test_register_email_already_taken():
    user_repo = MagicMock()
    user_repo.find_by_email = AsyncMock(return_value={"email": "existe@example.com"})

    with pytest.raises(EmailAlreadyTaken):
        await user_service.register(
            email="existe@example.com",
            password="motdepasse",
            user_repo=user_repo,
        )

    user_repo.create.assert_not_called()


async def test_login_ok():
    user_repo = MagicMock()
    user_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "email": "user@example.com",
        "password_hash": "hashed_value",
        "plan": "pro",
    }
    user_repo.find_by_email = AsyncMock(return_value=user_doc)

    with patch("app.services.user_service.verify_password", return_value=True):
        result = await user_service.login(
            email="user@example.com",
            password="bonmotdepasse",
            user_repo=user_repo,
        )

    assert result["user_id"] == "507f1f77bcf86cd799439011"
    assert result["plan"] == "pro"


async def test_login_invalid_credentials_user_not_found():
    user_repo = MagicMock()
    user_repo.find_by_email = AsyncMock(return_value=None)

    with pytest.raises(InvalidCredentials):
        await user_service.login(
            email="inconnu@example.com",
            password="nimporte",
            user_repo=user_repo,
        )


async def test_login_invalid_credentials_wrong_password():
    user_repo = MagicMock()
    user_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "email": "user@example.com",
        "password_hash": "hashed_value",
        "plan": "free",
    }
    user_repo.find_by_email = AsyncMock(return_value=user_doc)

    with patch("app.services.user_service.verify_password", return_value=False):
        with pytest.raises(InvalidCredentials):
            await user_service.login(
                email="user@example.com",
                password="mauvais",
                user_repo=user_repo,
            )


async def test_accept_terms_delegates_to_repo():
    user_repo = MagicMock()
    user_repo.set_terms_accepted = AsyncMock()

    await user_service.accept_terms(user_id="user_id_123", user_repo=user_repo)

    user_repo.set_terms_accepted.assert_awaited_once_with("user_id_123")
