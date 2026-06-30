from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

from config.settings import settings
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    hashed = pwd_context.hash(plain_password)
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    passwords_match = pwd_context.verify(plain_password, hashed_password)
    return passwords_match


def create_jwt(user_id: str, plan: str) -> str:
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "plan": plan,
        "exp": expiration_time,
    }

    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


def decode_jwt(token: str) -> dict:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    return payload


async def verify_access_token(token: str, user_repo: UserRepository) -> dict:
    """
    Logique métier d'authentification : décode le JWT et charge le user depuis la DB.
    Lève une ValueError si le token est invalide ou l'utilisateur introuvable.
    Pas d'import FastAPI ici — cette fonction est testable indépendamment.
    """
    try:
        payload = decode_jwt(token)
    except jwt.ExpiredSignatureError:
        raise ValueError("Session expirée, veuillez vous reconnecter")
    except jwt.InvalidTokenError:
        raise ValueError("Token invalide")

    user_id = payload.get("sub")
    if user_id is None:
        raise ValueError("Token invalide : champ 'sub' manquant")

    user = await user_repo.find_by_id(user_id)
    if user is None:
        raise ValueError("Utilisateur introuvable")

    return user
