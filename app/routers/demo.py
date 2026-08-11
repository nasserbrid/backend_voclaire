import asyncio

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.limiter import limiter
from app.logger import logger
from app.services import demo_service
from app.services.demo_service import DemoAudioTooLong, DemoTranscriptionFailed

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/stt")
@limiter.limit("5/minute")
async def demo_stt(request: Request, file: UploadFile = File(...)) -> dict:
    content_length = request.headers.get("content-length")
    if content_length is not None and int(content_length) > demo_service.DEMO_MAX_CONTENT_LENGTH_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux pour la démo. Créez un compte gratuit pour des fichiers plus longs.",
        )

    file_bytes = await file.read()

    try:
        return await asyncio.to_thread(
            demo_service.transcribe_demo,
            file_bytes=file_bytes,
            file_name=file.filename or "demo-audio",
            content_type=file.content_type or "application/octet-stream",
        )
    except DemoAudioTooLong:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio trop long pour la démo (10 minutes max). Créez un compte gratuit pour transcrire des fichiers plus longs.",
        )
    except DemoTranscriptionFailed as error:
        logger.error(f"[demo] Erreur ml-api : {error}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur lors de la transcription. Veuillez réessayer.",
        )
