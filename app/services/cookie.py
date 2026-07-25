from fastapi import Response

from config.settings import settings

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 jours


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.FRONTEND_URL.startswith("https://"),
        samesite="lax",
        max_age=COOKIE_MAX_AGE_SECONDS,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME)
