from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    company: str = Field(min_length=2, max_length=100)
    content: str = Field(min_length=10, max_length=500)
    rating: int = Field(ge=1, le=5)


class ReviewOut(BaseModel):
    id: str
    first_name: str
    company: str
    content: str
    rating: int
    plan: str
    created_at: datetime
