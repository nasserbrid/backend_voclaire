from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    content: str = Field(min_length=10, max_length=500)
    rating: int = Field(ge=1, le=5)


class ReviewOut(BaseModel):
    id: str
    author_name: str
    content: str
    rating: int
    plan: str
    created_at: datetime
