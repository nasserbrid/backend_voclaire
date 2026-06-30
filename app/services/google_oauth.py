import secrets
from typing import Optional
from urllib.parse import urlencode

import httpx

from config.settings import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

# Scopes demandés à Google : profil de base + email
GOOGLE_SCOPES = "openid email profile"


def build_google_auth_url(state: str) -> str:
    """Construit l'URL vers laquelle rediriger l'utilisateur pour qu'il se connecte avec Google."""
    params = {
        "client_id": settings.GOOGLE_ID_CLIENT_VOCLAIRE,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "state": state,
        "access_type": "offline",
    }

    # urlencode encode les espaces et caractères spéciaux (ex: scope "openid email profile" → "openid+email+profile")
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return auth_url


def generate_state() -> str:
    """Génère un token aléatoire pour protéger contre le CSRF."""
    state = secrets.token_urlsafe(32)
    return state


async def exchange_code_for_tokens(authorization_code: str) -> dict:
    """Échange le code reçu de Google contre un access_token Google."""
    payload = {
        "client_id": settings.GOOGLE_ID_CLIENT_VOCLAIRE,
        "client_secret": settings.GOOGLE_SECRET_CLIENT_VOCLAIRE,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": authorization_code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        response.raise_for_status()
        tokens = response.json()

    return tokens


async def get_google_user_info(access_token: str) -> dict:
    """Appelle l'API Google pour récupérer les infos du user (email, google_id...)."""
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(GOOGLE_USERINFO_URL, headers=headers)
        response.raise_for_status()
        user_info = response.json()

    return user_info
