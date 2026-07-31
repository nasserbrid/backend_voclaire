from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    MONGODB_URI: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 10080  # 7 jours
    CORS_ORIGINS: str = "http://localhost:5173"
    FRONTEND_URL: str = "http://localhost:5173"

    GOOGLE_ID_CLIENT_VOCLAIRE: str
    GOOGLE_SECRET_CLIENT_VOCLAIRE: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/auth/google/callback"

    # Étape 10 — ml-api + Cloudflare R2
    ML_API_URL: str = "http://localhost:8000"
    ML_API_INTERNAL_KEY: str = ""
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: str = "voclaire-audio"

    # Étape 11 — LLM post-traitement (OpenAI)
    OPENAI_API_KEY: str = ""
    LLM_FREE_MONTHLY_QUOTA: int = 10

    # Étape 13 — Paiement Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_PRICE_ID_MENSUEL: str = ""
    STRIPE_PRICE_ID_ANNUEL: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:5173/app?payment=success"
    STRIPE_CANCEL_URL: str = "http://localhost:5173/pricing"
    STRIPE_CUSTOMER_PORTAL_RETURN_URL: str = "http://localhost:5173/app"

    # Celery + Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email SMTP (confirmation paiement)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Monitoring erreurs (Sentry)
    SENTRY_DSN: str = ""

    # Logs centralisés (Better Stack)
    LOGTAIL_SOURCE_TOKEN: str = ""
    LOGTAIL_INGESTING_HOST: str = ""

    # Analytics produit (PostHog) — funnel signup → first_transcription → llm_call → upgrade
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://eu.i.posthog.com"

    def get_cors_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
