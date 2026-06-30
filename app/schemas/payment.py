from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    billing_period: str  # "monthly" ou "annual"
