from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import transcription_service
from app.services.transcription_service import QuotaExceeded, TranscriptionNotFound

# Doc MongoDB minimal retourné par find_one_by_id_and_user_id
TRANSCRIPTION_DOC = {
    "text": "Texte original de la transcription.",
    "file_name": "audio.mp3",
    "file_size": 2048,
    "duration_seconds": 45.0,
    "created_at": datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc),
}


async def test_improve_ok():
    transcription_repo = MagicMock()
    transcription_repo.find_one_by_id_and_user_id = AsyncMock(return_value=TRANSCRIPTION_DOC)
    transcription_repo.set_improved_text = AsyncMock()

    llm_usage_repo = MagicMock()
    llm_usage_repo.count_this_month = AsyncMock(return_value=3)  # en dessous du quota
    llm_usage_repo.record = AsyncMock()

    with patch("app.services.llm.improve_text", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Texte après correction orthographique."

        result = await transcription_service.improve(
            transcription_id="trans_id_123",
            user_id="user_id_abc",
            mode="correction",
            user_plan="free",
            transcription_repo=transcription_repo,
            llm_usage_repo=llm_usage_repo,
            free_quota=10,
        )

    assert result.improved_text == "Texte après correction orthographique."
    assert result.text == "Texte original de la transcription."
    assert result.id == "trans_id_123"
    transcription_repo.set_improved_text.assert_awaited_once_with(
        transcription_id="trans_id_123",
        improved_text="Texte après correction orthographique.",
    )
    llm_usage_repo.record.assert_awaited_once_with(user_id="user_id_abc")


async def test_improve_quota_exceeded_raises():
    transcription_repo = MagicMock()
    transcription_repo.find_one_by_id_and_user_id = AsyncMock(return_value=TRANSCRIPTION_DOC)

    llm_usage_repo = MagicMock()
    llm_usage_repo.count_this_month = AsyncMock(return_value=10)  # quota atteint

    with pytest.raises(QuotaExceeded):
        await transcription_service.improve(
            transcription_id="trans_id_123",
            user_id="user_id_abc",
            mode="correction",
            user_plan="free",
            transcription_repo=transcription_repo,
            llm_usage_repo=llm_usage_repo,
            free_quota=10,
        )


async def test_improve_transcription_not_found():
    transcription_repo = MagicMock()
    transcription_repo.find_one_by_id_and_user_id = AsyncMock(return_value=None)

    llm_usage_repo = MagicMock()

    with pytest.raises(TranscriptionNotFound):
        await transcription_service.improve(
            transcription_id="id_inexistant",
            user_id="user_id_abc",
            mode="correction",
            user_plan="free",
            transcription_repo=transcription_repo,
            llm_usage_repo=llm_usage_repo,
            free_quota=10,
        )


async def test_improve_pro_bypasses_quota_check():
    """Le plan Pro ne vérifie pas le quota LLM (peu importe count_this_month)."""
    transcription_repo = MagicMock()
    transcription_repo.find_one_by_id_and_user_id = AsyncMock(return_value=TRANSCRIPTION_DOC)
    transcription_repo.set_improved_text = AsyncMock()

    llm_usage_repo = MagicMock()
    llm_usage_repo.record = AsyncMock()

    with patch("app.services.llm.improve_text", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Résumé pro."

        result = await transcription_service.improve(
            transcription_id="trans_id_pro",
            user_id="user_pro_abc",
            mode="résumé",
            user_plan="pro",
            transcription_repo=transcription_repo,
            llm_usage_repo=llm_usage_repo,
            free_quota=10,
        )

    assert result.improved_text == "Résumé pro."
    # count_this_month ne doit jamais être appelé pour un utilisateur pro
    llm_usage_repo.count_this_month.assert_not_called()
