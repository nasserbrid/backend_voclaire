from datetime import datetime

from pydantic import BaseModel, Field


class ContactIn(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=10, max_length=1000)


class ContactOut(BaseModel):
    id: str
    user_id: str
    email: str
    subject: str
    message: str
    created_at: datetime
