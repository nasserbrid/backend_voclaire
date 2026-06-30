from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.user import build_user_document


class UserRepository:
    """Centralise toutes les opérations MongoDB sur la collection 'users'."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["users"]

    async def find_by_email(self, email: str) -> Optional[dict]:
        user = await self.collection.find_one({"email": email})
        return user

    async def find_by_id(self, user_id: str) -> Optional[dict]:
        object_id = ObjectId(user_id)
        user = await self.collection.find_one({"_id": object_id})
        return user

    async def find_by_google_id(self, google_id: str) -> Optional[dict]:
        user = await self.collection.find_one({"google_id": google_id})
        return user

    async def link_google_id(self, user_id: str, google_id: str) -> None:
        object_id = ObjectId(user_id)
        await self.collection.update_one(
            {"_id": object_id},
            {"$set": {"google_id": google_id}},
        )

    async def create(
        self,
        email: str,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        terms_accepted_at: Optional[datetime] = None,
    ) -> str:
        document = build_user_document(email, password_hash, google_id, terms_accepted_at)
        result = await self.collection.insert_one(document)
        inserted_id = str(result.inserted_id)
        return inserted_id

    async def set_plan(self, user_id: str, plan: str) -> None:
        object_id = ObjectId(user_id)
        await self.collection.update_one(
            {"_id": object_id},
            {"$set": {"plan": plan}},
        )

    async def set_stripe_customer_id(self, user_id: str, customer_id: str) -> None:
        object_id = ObjectId(user_id)
        await self.collection.update_one(
            {"_id": object_id},
            {"$set": {"stripe_customer_id": customer_id}},
        )

    async def find_by_stripe_customer_id(self, customer_id: str) -> Optional[dict]:
        user = await self.collection.find_one({"stripe_customer_id": customer_id})
        return user

    async def set_terms_accepted(self, user_id: str) -> None:
        object_id = ObjectId(user_id)
        await self.collection.update_one(
            {"_id": object_id},
            {"$set": {"terms_accepted_at": datetime.now(timezone.utc)}},
        )
