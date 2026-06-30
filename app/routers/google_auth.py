from fastapi import APIRouter, Cookie, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Optional

from app.dependencies import get_user_repository
from app.logger import logger
from app.repositories.user_repository import UserRepository
from app.services.auth import create_jwt
from app.services.cookie import set_auth_cookie
from app.services.google_oauth import (
    build_google_auth_url,
    exchange_code_for_tokens,
    generate_state,
    get_google_user_info,
)
from config.settings import settings

router = APIRouter(prefix="/auth", tags=["google-auth"])

# Nom du cookie temporaire qui stocke le state OAuth (protection CSRF)
OAUTH_STATE_COOKIE = "oauth_state"

# URL du frontend vers laquelle rediriger après connexion réussie
FRONTEND_URL = "http://localhost:5173"


@router.get("/google")
async def google_login() -> RedirectResponse:
    """
    Étape 1 : génère un state aléatoire, le stocke en cookie,
    puis redirige l'utilisateur vers la page de connexion Google.
    """
    state = generate_state()
    google_url = build_google_auth_url(state)

    # Le cookie doit être posé sur le RedirectResponse lui-même —
    # pas sur un objet Response injecté (qui serait ignoré car on retourne un autre objet)
    redirect = RedirectResponse(url=google_url)
    redirect.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        max_age=300,  # 5 minutes — largement suffisant pour que l'utilisateur se connecte
    )
    return redirect


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    oauth_state: Optional[str] = Cookie(default=None),
    user_repo: UserRepository = Depends(get_user_repository),
) -> RedirectResponse:
    """
    Étape 2 : Google redirige ici avec un code et le state.
    On vérifie le state, on échange le code, on récupère le user Google,
    on crée ou retrouve le user en base, puis on pose notre JWT cookie.
    """
    # Vérifier le state pour se protéger contre le CSRF
    if oauth_state is None or oauth_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State OAuth invalide ou expiré",
        )

    # Échanger le code contre un access_token Google
    try:
        tokens = await exchange_code_for_tokens(authorization_code=code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible d'échanger le code avec Google",
        )

    google_access_token = tokens["access_token"]

    # Récupérer les infos du user depuis l'API Google
    try:
        google_user = await get_google_user_info(access_token=google_access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Impossible de récupérer les informations Google",
        )

    google_id = google_user["sub"]   # identifiant unique Google
    email = google_user["email"]

    # Étape 1 : chercher par google_id (user déjà connecté via Google)
    user_by_google_id = await user_repo.find_by_google_id(google_id)

    if user_by_google_id is not None:
        user_id = str(user_by_google_id["_id"])
        user_plan = user_by_google_id["plan"]
        logger.info(f"Connexion Google (compte Google connu) : {email}")

    else:
        # Étape 2 : chercher par email (user inscrit par formulaire avec le même email)
        user_by_email = await user_repo.find_by_email(email)

        if user_by_email is not None:
            # Compte formulaire trouvé → on lie le google_id pour les prochaines connexions
            user_id = str(user_by_email["_id"])
            user_plan = user_by_email["plan"]
            await user_repo.link_google_id(user_id=user_id, google_id=google_id)
            logger.info(f"Liaison Google sur compte existant : {email}")

        else:
            # Aucun compte → nouvel utilisateur Google, sans mot de passe
            user_id = await user_repo.create(
                email=email,
                password_hash=None,
                google_id=google_id,
            )
            user_plan = "free"
            logger.info(f"Inscription via Google (nouveau compte) : {email}")

    # Générer notre JWT et le stocker dans un cookie HttpOnly
    # Même principe : cookies posés sur le RedirectResponse retourné, pas sur response injecté
    token = create_jwt(user_id=user_id, plan=user_plan)
    redirect = RedirectResponse(url=FRONTEND_URL, status_code=status.HTTP_302_FOUND)
    redirect.delete_cookie(key=OAUTH_STATE_COOKIE)  # nettoyer le cookie CSRF temporaire
    set_auth_cookie(redirect, token)
    return redirect
