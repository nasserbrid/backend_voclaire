from datetime import datetime, timezone

import httpx
import pymongo
from bson import ObjectId
from celery.exceptions import MaxRetriesExceededError

from app.celery_app import celery_app
from app.logger import logger
from app.services import audio_service
from app.services.analytics_service import capture
from app.services.r2 import _delete_sync, _download_sync
from app.services.transcription_service import (
    STT_FREE_MAX_ITEM_SECONDS,
    STT_FREE_MONTHLY_SECONDS_PER_CATEGORY,
)
from config.settings import settings


def _get_sync_db() -> pymongo.database.Database:
    client = pymongo.MongoClient(settings.MONGODB_URI)
    return client.get_default_database()


@celery_app.task(bind=True, max_retries=3)
def transcribe_audio(
    self,
    transcription_id: str,
    r2_key: str,
    file_name: str,
    content_type: str,
    user_id: str,
    user_plan: str,
    declared_duration_seconds: float,
    source: str,
) -> None:
    try:
        file_bytes = _download_sync(r2_key)

        # Ferme le soft gate ouvert à /confirm : declared_duration_seconds vient du
        # client, non fiable. On recalcule la vraie durée maintenant qu'on a les bytes.
        real_duration_seconds = audio_service.get_audio_duration_seconds(file_bytes)

        db = _get_sync_db()

        if user_plan == "free":
            quota_exceeded = real_duration_seconds > STT_FREE_MAX_ITEM_SECONDS
            if not quota_exceeded:
                now = datetime.now(timezone.utc)
                usage_doc = db["stt_usage"].find_one(
                    {"user_id": user_id, "year": now.year, "month": now.month, "source": source}
                )
                used = usage_doc["seconds_used"] if usage_doc else 0
                remaining = STT_FREE_MONTHLY_SECONDS_PER_CATEGORY - used
                quota_exceeded = real_duration_seconds > remaining
        else:
            quota_exceeded = False

        if quota_exceeded:
            logger.warning(
                f"[task] Quota dépassé après vérification réelle ({real_duration_seconds}s) : "
                f"{transcription_id} — ml-api jamais appelé"
            )
            _delete_sync(r2_key)
            db["transcriptions"].update_one(
                {"_id": ObjectId(transcription_id)},
                {"$set": {"status": "quota_exceeded"}},
            )
            return

        endpoint = "/stt/pro" if user_plan == "pro" else "/stt"
        ml_timeout = min(real_duration_seconds * 6 + 120, 86400.0)  # cap 24h
        logger.info(f"[task] Envoi '{file_name}' à ml-api{endpoint}")

        with httpx.Client(timeout=ml_timeout) as client:
            response = client.post(
                f"{settings.ML_API_URL}{endpoint}",
                files={"file": (file_name, file_bytes, content_type)},
                headers={"X-Internal-Api-Key": settings.ML_API_INTERNAL_KEY},
            )
            response.raise_for_status()

        data = response.json()
        text: str = data["text"]
        segments: list | None = data.get("segments")
        logger.info(f"[task] Transcription terminée : {transcription_id} ({len(text)} chars)")

        is_first_transcription = db["transcriptions"].count_documents(
            {"user_id": ObjectId(user_id), "status": "done"}
        ) == 0

        db["transcriptions"].update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {
                "text": text,
                "segments": segments,
                "status": "done",
                "duration_seconds": real_duration_seconds,
            }},
        )

        if is_first_transcription:
            capture(user_id, "first_transcription", {"source": source})

        if user_plan == "free":
            now = datetime.now(timezone.utc)
            db["stt_usage"].update_one(
                {"user_id": user_id, "year": now.year, "month": now.month, "source": source},
                {"$inc": {"seconds_used": int(real_duration_seconds)}},
                upsert=True,
            )

    except Exception as exc:
        logger.error(
            f"[task] Erreur transcription {transcription_id} "
            f"(tentative {self.request.retries + 1}) : {exc}"
        )
        try:
            raise self.retry(exc=exc, countdown=300)
        except MaxRetriesExceededError:
            logger.error(f"[task] Échec définitif : {transcription_id}")
            db = _get_sync_db()
            db["transcriptions"].update_one(
                {"_id": ObjectId(transcription_id)},
                {"$set": {"status": "error"}},
            )
