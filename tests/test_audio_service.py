from unittest.mock import MagicMock, patch

from app.services.audio_service import get_audio_duration_seconds


def test_get_audio_duration_seconds_returns_float():
    mock_segment = MagicMock()
    # len(segment) en ms : 7500 ms → 7.5 secondes
    mock_segment.__len__ = MagicMock(return_value=7500)

    with patch("app.services.audio_service.AudioSegment") as mock_audio_segment:
        mock_audio_segment.from_file.return_value = mock_segment
        result = get_audio_duration_seconds(b"fake audio bytes")

    assert result == 7.5
    mock_audio_segment.from_file.assert_called_once()


def test_get_audio_duration_seconds_zero_length():
    mock_segment = MagicMock()
    mock_segment.__len__ = MagicMock(return_value=0)

    with patch("app.services.audio_service.AudioSegment") as mock_audio_segment:
        mock_audio_segment.from_file.return_value = mock_segment
        result = get_audio_duration_seconds(b"")

    assert result == 0.0
