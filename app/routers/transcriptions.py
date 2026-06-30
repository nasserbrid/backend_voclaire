import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, UploadFile, status

from app.dependencies import (
    get_current_user,
    get_llm_usage_repository,
    get_stt_usage_repository,
    get_transcription_repository,
)
from app.limiter import limiter
from app.logger import logger
from app.repositories.llm_usage_repository import LlmUsageRepository
from app.repositories.stt_usage_repository import SttUsageRepository
from app.repositories.transcription_repository import TranscriptionRepository
from app.schemas.transcription import ImproveRequest, TranscriptionOut
from app.services import export_service, transcription_service
from app.services.auth import decode_jwt
from app.services.cookie import COOKIE_NAME
from app.services.transcription_service import (
    AudioTooLong,
    QuotaExceeded,
    SttQuotaExceeded,
    TranscriptionNotFound,
)
from config.settings import settings

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])


def _transcription_rate_limit(request: Request) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        try:
            payload = decode_jwt(token)
            if payload.get("plan") == "pro":
                return "20/minute"
        except Exception:
            pass
    return "3/minute"


@router.post("", response_model=TranscriptionOut, status_code=status.HTTP_201_CREATED)
@limiter.limit(_transcription_rate_limit)
async def create_transcription(
    request: Request,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
    stt_usage_repo: SttUsageRepository = Depends(get_stt_usage_repository),
) -> TranscriptionOut:
    file_bytes = await file.read()
    file_name = file.filename or "audio"
    content_type = file.content_type or "audio/mpeg"
    user_id = str(current_user["_id"])
    user_plan = current_user.get("plan", "free")

    try:
        return await transcription_service.create(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=content_type,
            user_id=user_id,
            user_plan=user_plan,
            transcription_repo=transcription_repo,
            stt_usage_repo=stt_usage_repo,
        )
    except AudioTooLong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier trop long. Les utilisateurs free sont limités à 30 minutes par audio.",
        )
    except SttQuotaExceeded as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota mensuel dépassé. Il vous reste {error.remaining_minutes} minute(s) ce mois-ci. Passez Pro pour une transcription illimitée.",
        )
    except httpx.HTTPStatusError as error:
        logger.error(f"Erreur ml-api {error.response.status_code} : {error.response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur lors de la transcription audio",
        )
    except httpx.RequestError as error:
        logger.error(f"ml-api injoignable : {error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service de transcription indisponible",
        )


@router.get("", response_model=list[TranscriptionOut])
async def get_transcriptions(
    current_user: dict = Depends(get_current_user),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> list[TranscriptionOut]:
    user_id = str(current_user["_id"])
    return await transcription_service.list_by_user(
        user_id=user_id,
        transcription_repo=transcription_repo,
    )


@router.delete("/{transcription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcription(
    transcription_id: str,
    current_user: dict = Depends(get_current_user),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> Response:
    user_id = str(current_user["_id"])

    try:
        await transcription_service.delete(
            transcription_id=transcription_id,
            user_id=user_id,
            transcription_repo=transcription_repo,
        )
    except TranscriptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription introuvable",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{transcription_id}/improve", response_model=TranscriptionOut)
async def improve_transcription(
    transcription_id: str,
    body: ImproveRequest,
    current_user: dict = Depends(get_current_user),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
    llm_usage_repo: LlmUsageRepository = Depends(get_llm_usage_repository),
) -> TranscriptionOut:
    user_id = str(current_user["_id"])
    user_plan = current_user.get("plan", "free")

    try:
        return await transcription_service.improve(
            transcription_id=transcription_id,
            user_id=user_id,
            mode=body.mode,
            user_plan=user_plan,
            transcription_repo=transcription_repo,
            llm_usage_repo=llm_usage_repo,
            free_quota=settings.LLM_FREE_MONTHLY_QUOTA,
        )
    except TranscriptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription introuvable",
        )
    except QuotaExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Quota mensuel atteint ({settings.LLM_FREE_MONTHLY_QUOTA}/{settings.LLM_FREE_MONTHLY_QUOTA}). Passez en Pro pour un accès illimité.",
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    except Exception as error:
        logger.error(f"Erreur LLM : {error}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur LLM",
        )


@router.get("/{transcription_id}/export")
async def export_transcription(
    transcription_id: str,
    format: str = Query(..., description="Format d'export : docx, pdf, pptx"),
    current_user: dict = Depends(get_current_user),
    transcription_repo: TranscriptionRepository = Depends(get_transcription_repository),
) -> Response:
    valid_formats = {"docx", "pdf", "pptx"}
    if format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format invalide. Valeurs acceptées : docx, pdf, pptx",
        )

    user_id = str(current_user["_id"])
    user_plan = current_user.get("plan", "free")

    transcription = await transcription_repo.find_one_by_id_and_user_id(
        transcription_id=transcription_id,
        user_id=user_id,
    )
    if transcription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription introuvable",
        )

    base_name = transcription["file_name"].rsplit(".", 1)[0]
    content_disposition = f'attachment; filename="{base_name}.{format}"'

    if format == "docx" and user_plan == "free":
        file_bytes = export_service.generate_docx_free(
            transcription_text=transcription["text"],
            file_name=transcription["file_name"],
        )
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return Response(content=file_bytes, media_type=media_type, headers={"Content-Disposition": content_disposition})

    if format in {"pdf", "pptx"} and user_plan == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Réservé au plan Pro",
        )

    structured_content = transcription.get("structured_content")

    if format == "docx" and user_plan == "pro":
        if structured_content is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Générez d'abord la réunion structurée",
            )
        file_bytes = export_service.generate_docx_pro(
            structured=structured_content,
            file_name=transcription["file_name"],
        )
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return Response(content=file_bytes, media_type=media_type, headers={"Content-Disposition": content_disposition})

    if format == "pdf" and user_plan == "pro":
        if structured_content is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Générez d'abord la réunion structurée",
            )
        file_bytes = export_service.generate_pdf_pro(
            structured=structured_content,
            file_name=transcription["file_name"],
        )
        return Response(content=file_bytes, media_type="application/pdf", headers={"Content-Disposition": content_disposition})

    if format == "pptx" and user_plan == "pro":
        if structured_content is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Générez d'abord la réunion structurée",
            )
        file_bytes = export_service.generate_pptx_pro(
            structured=structured_content,
            file_name=transcription["file_name"],
        )
        media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        return Response(content=file_bytes, media_type=media_type, headers={"Content-Disposition": content_disposition})

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Combinaison format/plan invalide")
