from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: str
    email: EmailStr
    plan: str
    created_at: datetime
    terms_accepted: bool
