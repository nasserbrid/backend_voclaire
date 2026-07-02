from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import contact_service

USER = {
    "_id": "user_id_abc",
    "email": "nasser@example.com",
    "plan": "free",
}

CONTACT_DOC = {
    "_id": "contact_id_xyz",
    "id": "contact_id_xyz",
    "user_id": "user_id_abc",
    "email": "nasser@example.com",
    "subject": "Problème de transcription",
    "message": "Bonjour, je rencontre un souci avec mon fichier audio.",
    "created_at": datetime(2026, 7, 2, 10, 0, 0, tzinfo=timezone.utc),
}


async def test_submit_contact_ok() -> None:
    """Le contact est créé et la notification email est envoyée."""
    contact_repo: MagicMock = MagicMock()
    contact_repo.create = AsyncMock(return_value=CONTACT_DOC)

    with patch(
        "app.services.contact_service.send_contact_notification",
        new_callable=AsyncMock,
    ) as mock_notify:
        result = await contact_service.submit(
            user=USER,
            subject="Problème de transcription",
            message="Bonjour, je rencontre un souci avec mon fichier audio.",
            contact_repo=contact_repo,
        )

    assert result["subject"] == "Problème de transcription"
    assert result["email"] == "nasser@example.com"
    assert result["user_id"] == "user_id_abc"

    contact_repo.create.assert_awaited_once_with(
        user_id="user_id_abc",
        email="nasser@example.com",
        subject="Problème de transcription",
        message="Bonjour, je rencontre un souci avec mon fichier audio.",
    )
    mock_notify.assert_awaited_once_with(
        from_email="nasser@example.com",
        from_plan="free",
        subject="Problème de transcription",
        message="Bonjour, je rencontre un souci avec mon fichier audio.",
    )


async def test_submit_contact_email_failure_does_not_raise() -> None:
    """Un échec d'envoi email ne propage pas l'erreur — le contact est quand même retourné."""
    contact_repo: MagicMock = MagicMock()
    contact_repo.create = AsyncMock(return_value=CONTACT_DOC)

    with patch(
        "app.services.contact_service.send_contact_notification",
        new_callable=AsyncMock,
        side_effect=Exception("SMTP unavailable"),
    ):
        result = await contact_service.submit(
            user=USER,
            subject="Problème de transcription",
            message="Bonjour, je rencontre un souci avec mon fichier audio.",
            contact_repo=contact_repo,
        )

    assert result == CONTACT_DOC
    contact_repo.create.assert_awaited_once()
