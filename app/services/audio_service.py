import io

from pydub import AudioSegment


def get_audio_duration_seconds(file_bytes: bytes) -> float:
    segment = AudioSegment.from_file(io.BytesIO(file_bytes))
    duration = len(segment) / 1000.0
    return duration
