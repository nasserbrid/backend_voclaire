import stripe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.limiter import limiter, rate_limit_handler
from app.logger import logger
from app.routers import auth, google_auth, payments, reviews, transcriptions, users
from config.settings import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

app = FastAPI(title="voclaire-backend", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(google_auth.router)
app.include_router(users.router)
app.include_router(transcriptions.router)
app.include_router(payments.router)
app.include_router(reviews.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


logger.info("voclaire-backend démarré")
