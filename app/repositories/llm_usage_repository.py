from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


class LlmUsageRepository:
    """Centralise toutes les opérations MongoDB sur la collection 'llm_usage'."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["llm_usage"]

    async def count_this_month(self, user_id: str) -> int:
        now = datetime.now(timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        count = await self.collection.count_documents({
            "user_id": ObjectId(user_id),
            "created_at": {"$gte": month_start},
        })
        return count

    async def record(self, user_id: str) -> None:
        document = {
            "user_id": ObjectId(user_id),
            "created_at": datetime.now(timezone.utc),
        }
        await self.collection.insert_one(document)
