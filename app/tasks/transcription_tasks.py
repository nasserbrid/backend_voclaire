from datetime import datetime, timezone

import httpx
import pymongo
from bson import ObjectId
from celery.exceptions import MaxRetriesExceededError

from app.celery_app import celery_app
from app.logger import logger
from app.services.r2 import _download_sync
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
    duration_seconds: float,
) -> None:
    try:
        file_bytes = _download_sync(r2_key)

        endpoint = "/stt/pro" if user_plan == "pro" else "/stt"
        ml_timeout = 1200.0 if user_plan == "pro" else 120.0
        logger.info(f"[task] Envoi '{file_name}' à ml-api{endpoint}")

        with httpx.Client(timeout=ml_timeout) as client:
            response = client.post(
                f"{settings.ML_API_URL}{endpoint}",
                files={"file": (file_name, file_bytes, content_type)},
            )
            response.raise_for_status()

        text: str = response.json()["text"]
        logger.info(f"[task] Transcription terminée : {transcription_id} ({len(text)} chars)")

        db = _get_sync_db()
        db["transcriptions"].update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"text": text, "status": "done"}},
        )

        if user_plan == "free":
            now = datetime.now(timezone.utc)
            db["stt_usage"].update_one(
                {"user_id": user_id, "year": now.year, "month": now.month},
                {"$inc": {"seconds_used": int(duration_seconds)}},
                upsert=True,
            )

    except Exception as exc:
        logger.error(f"[task] Erreur transcription {transcription_id} (tentative {self.request.retries + 1}) : {exc}")
        try:
            raise self.retry(exc=exc, countdown=300)
        except MaxRetriesExceededError:
            logger.error(f"[task] Échec définitif : {transcription_id}")
            db = _get_sync_db()
            db["transcriptions"].update_one(
                {"_id": ObjectId(transcription_id)},
                {"$set": {"status": "error"}},
            )
