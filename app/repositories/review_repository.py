from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.review import build_review_document


class ReviewRepository:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["reviews"]

    async def create(
        self,
        user_id: str,
        first_name: str,
        company: str,
        plan: str,
        content: str,
        rating: int,
    ) -> dict:
        document = build_review_document(
            user_id=user_id,
            first_name=first_name,
            company=company,
            plan=plan,
            content=content,
            rating=rating,
        )
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return document

    async def find_by_user_id(self, user_id: str) -> Optional[dict]:
        return await self.collection.find_one({"user_id": ObjectId(user_id)})

    async def get_visible(self, limit: int = 20) -> list[dict]:
        cursor = (
            self.collection
            .find({
                "is_visible": True,
                "first_name": {"$exists": True},
                "company": {"$exists": True},
            })
            .sort("created_at", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)
