import asyncio

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_current_user, get_user_repository
from app.logger import logger
from app.repositories.user_repository import UserRepository
from app.schemas.payment import CheckoutRequest
from app.services import payment_service
from app.services.email_service import send_payment_confirmation
from config.settings import settings

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout")
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    if current_user.get("plan") == "pro":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous êtes déjà Pro",
        )

    if body.billing_period == "monthly":
        price_id = settings.STRIPE_PRICE_ID_MENSUEL
    else:
        price_id = settings.STRIPE_PRICE_ID_ANNUEL

    user_id = str(current_user["_id"])
    user_email = current_user["email"]

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        client_reference_id=user_id,
        customer_email=user_email,
        metadata={"billing_period": body.billing_period},
    )

    checkout_url = session.url
    logger.info(f"Session checkout créée pour user {user_id} ({body.billing_period})")
    return {"url": checkout_url}


@router.post("/portal")
async def create_portal_session(
    current_user: dict = Depends(get_current_user),
) -> dict:
    stripe_customer_id = current_user.get("stripe_customer_id")
    if stripe_customer_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun abonnement actif",
        )

    portal_session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=settings.STRIPE_CUSTOMER_PORTAL_RETURN_URL,
    )

    portal_url = portal_session.url
    logger.info(f"Session portail créée pour customer {stripe_customer_id}")
    return {"url": portal_url}


@router.post("/test-email")
async def test_email(body: dict) -> dict:
    to_email = body.get("email", "")
    if not to_email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Champ 'email' requis",
        )
    billing_period = body.get("billing_period", "monthly")
    try:
        await asyncio.to_thread(send_payment_confirmation, to_email, billing_period)
    except Exception as email_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(email_error),
        )
    return {"ok": True}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
) -> dict:
    body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signature invalide",
        )

    event_type = event["type"]
    logger.info(f"Webhook Stripe reçu : {event_type}")

    if event_type == "checkout.session.completed":
        session_data = event["data"]["object"]
        user_id = session_data["client_reference_id"]
        customer_id = session_data["customer"]
        try:
            user_email = session_data["customer_email"] or ""
        except (KeyError, TypeError):
            user_email = ""
        if not user_email and user_id:
            user = await user_repo.find_by_id(user_id)
            if user is not None:
                user_email = user["email"]
                logger.info(f"Email récupéré depuis MongoDB pour user {user_id}")
        try:
            billing_period = session_data["metadata"]["billing_period"]
        except (KeyError, TypeError):
            billing_period = "monthly"
        await payment_service.activate_pro(user_id, customer_id, user_repo)
        try:
            await asyncio.to_thread(send_payment_confirmation, user_email, billing_period)
        except Exception as email_error:
            logger.warning(f"Échec envoi email confirmation : {email_error}")

    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]
        await payment_service.deactivate_pro(customer_id, user_repo)

    return {"status": "ok"}
