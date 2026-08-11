from typing import Optional
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.demo_service import (
    DEMO_MAX_DURATION_SECONDS,
    DemoAudioTooLong,
    DemoTranscriptionFailed,
    transcribe_demo,
)
from config.settings import settings

FILE_NAME: str = "demo-audio.webm"
CONTENT_TYPE: str = "audio/webm"
TRANSCRIBED_TEXT: str = "bonjour le monde"


def _make_mock_http_client(
    json_response: dict,
    raise_status: Optional[Exception] = None,
) -> MagicMock:
    """Mock de httpx.Client utilisable comme context manager (même pattern que test_transcription_tasks.py)."""
    mock_response: MagicMock = MagicMock()
    mock_response.json.return_value = json_response
    if raise_status is not None:
        mock_response.raise_for_status.side_effect = raise_status

    mock_client: MagicMock = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    return mock_client


def test_transcribe_demo_success() -> None:
    mock_http_client: MagicMock = _make_mock_http_client(
        json_response={"text": TRANSCRIBED_TEXT, "segments": [{"speaker": "SPEAKER_00", "text": TRANSCRIBED_TEXT}]},
    )

    with patch("app.services.demo_service.audio_service.get_audio_duration_seconds", return_value=60.0), \
         patch("httpx.Client", return_value=mock_http_client):

        result = transcribe_demo(file_bytes=b"audio_bytes", file_name=FILE_NAME, content_type=CONTENT_TYPE)

    assert result == {
        "text": TRANSCRIBED_TEXT,
        "segments": [{"speaker": "SPEAKER_00", "text": TRANSCRIBED_TEXT}],
    }
    _args, call_kwargs = mock_http_client.post.call_args
    assert call_kwargs["headers"] == {"X-Internal-Api-Key": settings.ML_API_INTERNAL_KEY}


def test_transcribe_demo_audio_too_long() -> None:
    with patch(
        "app.services.demo_service.audio_service.get_audio_duration_seconds",
        return_value=DEMO_MAX_DURATION_SECONDS + 1,
    ), patch("httpx.Client") as mock_httpx_client_class:

        with pytest.raises(DemoAudioTooLong):
            transcribe_demo(file_bytes=b"audio_bytes", file_name=FILE_NAME, content_type=CONTENT_TYPE)

    mock_httpx_client_class.assert_not_called()


def test_transcribe_demo_ml_api_failure() -> None:
    http_error: httpx.HTTPStatusError = httpx.HTTPStatusError(
        "500 Server Error",
        request=MagicMock(),
        response=MagicMock(status_code=500),
    )
    mock_http_client: MagicMock = _make_mock_http_client(json_response={}, raise_status=http_error)

    with patch("app.services.demo_service.audio_service.get_audio_duration_seconds", return_value=60.0), \
         patch("httpx.Client", return_value=mock_http_client):

        with pytest.raises(DemoTranscriptionFailed):
            transcribe_demo(file_bytes=b"audio_bytes", file_name=FILE_NAME, content_type=CONTENT_TYPE)
