import asyncio

import boto3
from botocore.client import BaseClient

from app.logger import logger
from config.settings import settings


def _get_r2_client() -> BaseClient:
    endpoint_url = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )
    return client


def _upload_sync(file_bytes: bytes, key: str, content_type: str) -> str:
    client = _get_r2_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    logger.info(f"Audio uploadé sur R2 : {key}")
    return key


async def upload_audio(file_bytes: bytes, key: str, content_type: str) -> str:
    # boto3 est synchrone — on l'exécute dans un thread pour ne pas bloquer la boucle async
    r2_key = await asyncio.to_thread(_upload_sync, file_bytes, key, content_type)
    return r2_key


def _delete_sync(key: str) -> None:
    client = _get_r2_client()
    client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    logger.info(f"Audio supprimé de R2 : {key}")


async def delete_audio(key: str) -> None:
    await asyncio.to_thread(_delete_sync, key)
