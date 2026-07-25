from motor.motor_asyncio import AsyncIOMotorDatabase


class SttUsageRepository:
    """Suivi mensuel des secondes de transcription consommées par utilisateur free,
    par catégorie ('file' ou 'recording') — deux compteurs indépendants."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["stt_usage"]

    async def get_seconds_used(self, user_id: str, year: int, month: int, source: str) -> int:
        document = await self.collection.find_one(
            {"user_id": user_id, "year": year, "month": month, "source": source}
        )
        if document is None:
            return 0
        seconds_used = document.get("seconds_used", 0)
        return seconds_used

    async def add_seconds(
        self, user_id: str, year: int, month: int, source: str, seconds: int
    ) -> None:
        await self.collection.update_one(
            {"user_id": user_id, "year": year, "month": month, "source": source},
            {"$inc": {"seconds_used": seconds}},
            upsert=True,
        )
