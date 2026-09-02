from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_current_user
from app.limiter import limiter
from app.logger import logger
from app.schemas.chat import ChatIn, ChatOut
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatOut)
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatIn,
    current_user: dict = Depends(get_current_user),
) -> ChatOut:
    try:
        reply = await chat_service.answer(
            user=current_user,
            message=body.message,
            history=body.history,
        )
    except Exception as error:
        logger.error(f"Erreur chatbot : {error}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur chatbot",
        )
    return ChatOut(reply=reply)
