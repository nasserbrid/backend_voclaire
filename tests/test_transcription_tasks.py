from typing import Optional
from unittest.mock import MagicMock, patch

import httpx
from bson import ObjectId
from celery.exceptions import MaxRetriesExceededError

from app.tasks.transcription_tasks import transcribe_audio

TRANSCRIPTION_ID: str = "66a1b2c3d4e5f6789abc1234"
R2_KEY: str = "user123/uuid-audio.mp3"
FILE_NAME: str = "audio.mp3"
CONTENT_TYPE: str = "audio/mpeg"
USER_ID: str = "user123"
DURATION_SECONDS: float = 45.0
TRANSCRIBED_TEXT: str = "bonjour le monde"


def _make_mock_http_client(
    json_response: dict,
    raise_status: Optional[Exception] = None,
) -> MagicMock:
    """Mock de httpx.Client utilisable comme context manager."""
    mock_response: MagicMock = MagicMock()
    mock_response.json.return_value = json_response
    if raise_status is not None:
        mock_response.raise_for_status.side_effect = raise_status

    mock_client: MagicMock = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    return mock_client


def _task_kwargs(user_plan: str = "free") -> dict:
    """Arguments standard passés à la tâche Celery."""
    return {
        "transcription_id": TRANSCRIPTION_ID,
        "r2_key": R2_KEY,
        "file_name": FILE_NAME,
        "content_type": CONTENT_TYPE,
        "user_id": USER_ID,
        "user_plan": user_plan,
        "duration_seconds": DURATION_SECONDS,
    }


def test_transcribe_audio_success() -> None:
    """Transcription réussie : update_one avec status=done + stt_usage mis à jour (free)."""
    mock_http_client: MagicMock = _make_mock_http_client(
        json_response={"text": TRANSCRIBED_TEXT},
    )

    # MagicMock.__getitem__ retourne le même objet pour toutes les clés par défaut.
    # side_effect permet de distinguer les collections MongoDB.
    mock_transcriptions: MagicMock = MagicMock()
    mock_stt_usage: MagicMock = MagicMock()
    mock_db: MagicMock = MagicMock()
    mock_db.__getitem__.side_effect = lambda key: (
        mock_transcriptions if key == "transcriptions" else mock_stt_usage
    )

    with patch("app.tasks.transcription_tasks._download_sync", return_value=b"audio_bytes"), \
         patch("httpx.Client", return_value=mock_http_client), \
         patch("app.tasks.transcription_tasks._get_sync_db", return_value=mock_db):

        transcribe_audio.apply(kwargs=_task_kwargs("free"))

    expected_oid: ObjectId = ObjectId(TRANSCRIPTION_ID)
    mock_transcriptions.update_one.assert_called_once_with(
        {"_id": expected_oid},
        {"$set": {"text": TRANSCRIBED_TEXT, "segments": None, "status": "done"}},
    )
    mock_stt_usage.update_one.assert_called_once()


def test_transcribe_audio_ml_api_failure() -> None:
    """Un HTTP 500 de ml-api épuise les retries et force status=error en MongoDB."""
    http_error: httpx.HTTPStatusError = httpx.HTTPStatusError(
        "500 Server Error",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )
    mock_http_client: MagicMock = _make_mock_http_client(
        json_response={},
        raise_status=http_error,
    )
    mock_db: MagicMock = MagicMock()

    with patch.object(transcribe_audio, "retry", side_effect=MaxRetriesExceededError()), \
         patch("app.tasks.transcription_tasks._download_sync", return_value=b"audio_bytes"), \
         patch("httpx.Client", return_value=mock_http_client), \
         patch("app.tasks.transcription_tasks._get_sync_db", return_value=mock_db):

        transcribe_audio.apply(kwargs=_task_kwargs("free"))

    expected_oid: ObjectId = ObjectId(TRANSCRIPTION_ID)
    mock_db["transcriptions"].update_one.assert_called_once_with(
        {"_id": expected_oid},
        {"$set": {"status": "error"}},
    )


def test_transcribe_audio_download_failure() -> None:
    """Un échec R2 (_download_sync) épuise les retries et force status=error en MongoDB."""
    mock_db: MagicMock = MagicMock()

    with patch.object(transcribe_audio, "retry", side_effect=MaxRetriesExceededError()), \
         patch("app.tasks.transcription_tasks._download_sync", side_effect=ConnectionError("R2 unreachable")), \
         patch("app.tasks.transcription_tasks._get_sync_db", return_value=mock_db):

        transcribe_audio.apply(kwargs=_task_kwargs("free"))

    expected_oid: ObjectId = ObjectId(TRANSCRIPTION_ID)
    mock_db["transcriptions"].update_one.assert_called_once_with(
        {"_id": expected_oid},
        {"$set": {"status": "error"}},
    )
