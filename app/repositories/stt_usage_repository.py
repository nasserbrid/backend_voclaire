from motor.motor_asyncio import AsyncIOMotorDatabase


class SttUsageRepository:
    """Suivi mensuel des secondes de transcription consommées par utilisateur free."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["stt_usage"]

    async def get_seconds_used(self, user_id: str, year: int, month: int) -> int:
        document = await self.collection.find_one(
            {"user_id": user_id, "year": year, "month": month}
        )
        if document is None:
            return 0
        seconds_used = document.get("seconds_used", 0)
        return seconds_used

    async def add_seconds(self, user_id: str, year: int, month: int, seconds: int) -> None:
        await self.collection.update_one(
            {"user_id": user_id, "year": year, "month": month},
            {"$inc": {"seconds_used": seconds}},
            upsert=True,
        )
