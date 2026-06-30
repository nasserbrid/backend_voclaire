from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.dependencies import get_user_repository
from app.limiter import limiter
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, MessageResponse, RegisterRequest
from app.services.auth import create_jwt
from app.services.cookie import clear_auth_cookie, set_auth_cookie
from app.services import user_service
from app.services.user_service import EmailAlreadyTaken, InvalidCredentials

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository),
) -> MessageResponse:
    try:
        result = await user_service.register(email=body.email, password=body.password, user_repo=user_repo)
    except EmailAlreadyTaken:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cet email est déjà utilisé")

    token = create_jwt(user_id=result["user_id"], plan=result["plan"])
    set_auth_cookie(response, token)
    return MessageResponse(message="Inscription réussie")


@router.post("/login", response_model=MessageResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    user_repo: UserRepository = Depends(get_user_repository),
) -> MessageResponse:
    try:
        result = await user_service.login(email=body.email, password=body.password, user_repo=user_repo)
    except InvalidCredentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    token = create_jwt(user_id=result["user_id"], plan=result["plan"])
    set_auth_cookie(response, token)
    return MessageResponse(message="Connexion réussie")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    clear_auth_cookie(response)
    return MessageResponse(message="Déconnexion réussie")
