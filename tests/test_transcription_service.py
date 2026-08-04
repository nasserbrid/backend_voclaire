from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import transcription_service
from app.services.transcription_service import InvalidR2Key, QuotaExceeded, TranscriptionNotFound

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

    with patch("app.services.llm.improve_text", new_callable=AsyncMock) as mock_llm, \
         patch("app.services.transcription_service.capture") as mock_capture:
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
    mock_capture.assert_called_once_with("user_id_abc", "llm_call", {"mode": "correction"})
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

    with patch("app.services.llm.improve_text", new_callable=AsyncMock) as mock_llm, \
         patch("app.services.transcription_service.capture"):
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


async def test_confirm_forwards_num_speakers_to_celery_task():
    """confirm() doit transmettre num_speakers à transcribe_audio.delay() sans le modifier."""
    transcription_repo = MagicMock()
    transcription_repo.create = AsyncMock(return_value="trans_id_456")

    stt_usage_repo = MagicMock()

    with patch("app.tasks.transcription_tasks.transcribe_audio.delay") as mock_delay:
        await transcription_service.confirm(
            user_id="user_id_abc",
            user_plan="pro",
            r2_key="user_id_abc/uuid-audio.mp3",
            file_name="audio.mp3",
            content_type="audio/mpeg",
            file_size=2048,
            duration_seconds=60.0,
            source="file",
            transcription_repo=transcription_repo,
            stt_usage_repo=stt_usage_repo,
            num_speakers=2,
        )

    mock_delay.assert_called_once_with(
        transcription_id="trans_id_456",
        r2_key="user_id_abc/uuid-audio.mp3",
        file_name="audio.mp3",
        content_type="audio/mpeg",
        user_id="user_id_abc",
        user_plan="pro",
        declared_duration_seconds=60.0,
        source="file",
        num_speakers=2,
    )


async def test_confirm_rejects_r2_key_not_owned_by_user():
    """Un r2_key ne commençant pas par '{user_id}/' doit être rejeté avant toute autre logique (IDOR)."""
    transcription_repo = MagicMock()
    transcription_repo.create = AsyncMock()

    stt_usage_repo = MagicMock()
    stt_usage_repo.get_seconds_used = AsyncMock()

    with pytest.raises(InvalidR2Key):
        await transcription_service.confirm(
            user_id="user_id_abc",
            user_plan="free",
            r2_key="autre_user_id/uuid-audio.mp3",
            file_name="audio.mp3",
            content_type="audio/mpeg",
            file_size=2048,
            duration_seconds=60.0,
            source="file",
            transcription_repo=transcription_repo,
            stt_usage_repo=stt_usage_repo,
        )

    transcription_repo.create.assert_not_called()
    stt_usage_repo.get_seconds_used.assert_not_called()
