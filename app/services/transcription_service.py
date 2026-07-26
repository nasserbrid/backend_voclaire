import uuid
from datetime import datetime, timezone
from typing import Optional

from app.logger import logger
from app.repositories.llm_usage_repository import LlmUsageRepository
from app.repositories.stt_usage_repository import SttUsageRepository
from app.repositories.transcription_repository import TranscriptionRepository
from app.schemas.transcription import TranscriptionOut
from app.services import llm, r2
from config.settings import settings

STT_FREE_MONTHLY_SECONDS_PER_CATEGORY = 4 * 60 * 60  # 4h/mois, par catégorie (file/recording)
STT_FREE_MAX_ITEM_SECONDS = 2 * 60 * 60              # 2h max par élément individuel


class TranscriptionNotFound(Exception):
    pass


class QuotaExceeded(Exception):
    pass


class AudioTooLong(Exception):
    pass


class SttQuotaExceeded(Exception):
    def __init__(self, remaining_minutes: int) -> None:
        self.remaining_minutes = remaining_minutes


def _doc_to_out(doc: dict) -> TranscriptionOut:
    return TranscriptionOut(
        id=str(doc["_id"]),
        status=doc.get("status", "done"),
        text=doc.get("text"),
        improved_text=doc.get("improved_text"),
        structured_content=doc.get("structured_content"),
        segments=doc.get("segments"),
        file_name=doc["file_name"],
        file_size=doc["file_size"],
        duration_seconds=doc.get("duration_seconds"),
        created_at=doc["created_at"],
    )


async def presign(
    user_id: str,
    file_name: str,
    content_type: str,
) -> tuple[str, str]:
    r2_key = f"{user_id}/{uuid.uuid4()}-{file_name}"
    upload_url = await r2.generate_presigned_upload_url(key=r2_key, content_type=content_type)
    return upload_url, r2_key


async def confirm(
    user_id: str,
    user_plan: str,
    r2_key: str,
    file_name: str,
    content_type: str,
    file_size: int,
    duration_seconds: float,
    source: str,
    transcription_repo: TranscriptionRepository,
    stt_usage_repo: SttUsageRepository,
) -> TranscriptionOut:
    now = datetime.now(timezone.utc)

    # Soft gate : duration_seconds est déclarée par le client, non vérifiée ici.
    # La tâche Celery recalcule la vraie durée après téléchargement depuis R2.
    if user_plan == "free":
        if duration_seconds > STT_FREE_MAX_ITEM_SECONDS:
            raise AudioTooLong()
        used = await stt_usage_repo.get_seconds_used(user_id, now.year, now.month, source)
        remaining = STT_FREE_MONTHLY_SECONDS_PER_CATEGORY - used
        if duration_seconds > remaining:
            remaining_minutes = int(remaining // 60)
            raise SttQuotaExceeded(remaining_minutes)

    transcription_id = await transcription_repo.create(
        user_id=user_id,
        file_name=file_name,
        file_size=file_size,
        r2_key=r2_key,
        duration_seconds=duration_seconds,
    )
    logger.info(f"Transcription créée (en attente) : {transcription_id}")

    from app.tasks.transcription_tasks import transcribe_audio
    transcribe_audio.delay(
        transcription_id=transcription_id,
        r2_key=r2_key,
        file_name=file_name,
        content_type=content_type,
        user_id=user_id,
        user_plan=user_plan,
        declared_duration_seconds=duration_seconds,
        source=source,
    )

    return TranscriptionOut(
        id=transcription_id,
        status="processing",
        text=None,
        file_name=file_name,
        file_size=file_size,
        duration_seconds=duration_seconds,
        created_at=now,
    )


async def list_by_user(
    user_id: str,
    transcription_repo: TranscriptionRepository,
) -> list[TranscriptionOut]:
    documents = await transcription_repo.find_by_user_id(user_id=user_id)
    return [_doc_to_out(doc) for doc in documents]


async def get_by_id(
    transcription_id: str,
    user_id: str,
    transcription_repo: TranscriptionRepository,
) -> TranscriptionOut:
    document = await transcription_repo.find_one_by_id_and_user_id(
        transcription_id=transcription_id,
        user_id=user_id,
    )
    if document is None:
        raise TranscriptionNotFound()
    return _doc_to_out(document)


async def improve(
    transcription_id: str,
    user_id: str,
    mode: str,
    user_plan: str,
    transcription_repo: TranscriptionRepository,
    llm_usage_repo: LlmUsageRepository,
    free_quota: int,
) -> TranscriptionOut:
    transcription = await transcription_repo.find_one_by_id_and_user_id(
        transcription_id=transcription_id,
        user_id=user_id,
    )
    if transcription is None:
        raise TranscriptionNotFound()

    if mode == "structured_meeting":
        if user_plan != "pro":
            raise ValueError("Mode réservé au plan Pro")
        structured_content = await llm.improve_text(text=transcription["text"], mode="structured_meeting")
        await transcription_repo.set_structured_content(
            transcription_id=transcription_id,
            content=structured_content,
        )
        logger.info(f"Réunion structurée sauvegardée : {transcription_id}")
        return TranscriptionOut(
            id=transcription_id,
            status=transcription.get("status", "done"),
            text=transcription.get("text"),
            improved_text=transcription.get("improved_text"),
            structured_content=structured_content,
            file_name=transcription["file_name"],
            file_size=transcription["file_size"],
            duration_seconds=transcription.get("duration_seconds"),
            created_at=transcription["created_at"],
        )

    if user_plan == "free":
        usage_count = await llm_usage_repo.count_this_month(user_id=user_id)
        if usage_count >= free_quota:
            raise QuotaExceeded()

    improved = await llm.improve_text(text=transcription["text"], mode=mode)

    await transcription_repo.set_improved_text(
        transcription_id=transcription_id,
        improved_text=improved,  # type: ignore[arg-type]
    )
    await llm_usage_repo.record(user_id=user_id)
    logger.info(f"Amélioration LLM sauvegardée : {transcription_id} (mode={mode})")

    return TranscriptionOut(
        id=transcription_id,
        status=transcription.get("status", "done"),
        text=transcription.get("text"),
        improved_text=improved,  # type: ignore[arg-type]
        file_name=transcription["file_name"],
        file_size=transcription["file_size"],
        duration_seconds=transcription.get("duration_seconds"),
        created_at=transcription["created_at"],
    )


async def delete(
    transcription_id: str,
    user_id: str,
    transcription_repo: TranscriptionRepository,
) -> None:
    document = await transcription_repo.find_one_by_id_and_user_id(
        transcription_id=transcription_id,
        user_id=user_id,
    )
    if document is None:
        raise TranscriptionNotFound()

    r2_key = document["r2_key"]

    await transcription_repo.delete_by_id(transcription_id=transcription_id)
    logger.info(f"Transcription supprimée de MongoDB : {transcription_id}")

    try:
        await r2.delete_audio(key=r2_key)
    except Exception as error:
        logger.warning(f"Échec suppression R2 (orphelin) pour la clé '{r2_key}' : {error}")
