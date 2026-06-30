from fastapi import Response

COOKIE_NAME = "access_token"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 jours


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,   # Passer à True en production (HTTPS)
        samesite="lax",
        max_age=COOKIE_MAX_AGE_SECONDS,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME)
