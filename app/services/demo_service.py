import httpx

from app.services import audio_service
from config.settings import settings

DEMO_MAX_DURATION_SECONDS = 10 * 60  # 10 min — aligné sur DEMO_MAX_MINUTES (frontend_voclaire), volontairement bien plus strict que STT_FREE_MAX_ITEM_SECONDS (2h) : pas de compte, pas de quota mensuel pour absorber l'abus
DEMO_MAX_CONTENT_LENGTH_BYTES = 50 * 1024 * 1024  # 50 Mo — marge large pour ~10 min même non compressé
DEMO_TIMEOUT_SECONDS = 180.0


class DemoAudioTooLong(Exception):
    pass


class DemoTranscriptionFailed(Exception):
    pass


def transcribe_demo(file_bytes: bytes, file_name: str, content_type: str) -> dict:
    duration_seconds = audio_service.get_audio_duration_seconds(file_bytes)
    if duration_seconds > DEMO_MAX_DURATION_SECONDS:
        raise DemoAudioTooLong()

    try:
        with httpx.Client(timeout=DEMO_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{settings.ML_API_URL}/stt",
                files={"file": (file_name, file_bytes, content_type)},
                headers={"X-Internal-Api-Key": settings.ML_API_INTERNAL_KEY},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as error:
        raise DemoTranscriptionFailed(str(error)) from error

    return {"text": data["text"], "segments": data.get("segments")}
