import logging

from config.settings import settings

logger = logging.getLogger("voclaire-backend")
logger.setLevel(logging.INFO)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(stream_handler)

    if settings.LOGTAIL_SOURCE_TOKEN:
        from logtail import LogtailHandler

        logtail_handler = LogtailHandler(
            source_token=settings.LOGTAIL_SOURCE_TOKEN,
            host=f"https://{settings.LOGTAIL_INGESTING_HOST}",
        )
        logger.addHandler(logtail_handler)
