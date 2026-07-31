import posthog

from app.logger import logger
from config.settings import settings

posthog.api_key = settings.POSTHOG_API_KEY
posthog.host = settings.POSTHOG_HOST


def capture(distinct_id: str, event: str, properties: dict | None = None) -> None:
    try:
        posthog.capture(distinct_id=distinct_id, event=event, properties=properties or {})
    except Exception:
        logger.warning(f"[analytics] échec capture event '{event}'", exc_info=True)
