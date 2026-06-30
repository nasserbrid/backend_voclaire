from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.transcription import build_transcription_document


class TranscriptionRepository:
    """Centralise toutes les opérations MongoDB sur la collection 'transcriptions'."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["transcriptions"]

    async def create(
        self,
        user_id: str,
        text: str,
        file_name: str,
        file_size: int,
        r2_key: str,
        duration_seconds: Optional[float] = None,
    ) -> str:
        document = build_transcription_document(
            user_id=user_id,
            text=text,
            file_name=file_name,
            file_size=file_size,
            r2_key=r2_key,
            duration_seconds=duration_seconds,
        )
        result = await self.collection.insert_one(document)
        inserted_id = str(result.inserted_id)
        return inserted_id

    async def find_by_user_id(self, user_id: str, limit: int = 20) -> list[dict]:
        object_id = ObjectId(user_id)
        cursor = (
            self.collection
            .find({"user_id": object_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        transcriptions = await cursor.to_list(length=limit)
        return transcriptions

    async def find_one_by_id_and_user_id(self, transcription_id: str, user_id: str) -> Optional[dict]:
        document = await self.collection.find_one({
            "_id": ObjectId(transcription_id),
            "user_id": ObjectId(user_id),
        })
        return document

    async def delete_by_id(self, transcription_id: str) -> None:
        await self.collection.delete_one({"_id": ObjectId(transcription_id)})

    async def set_improved_text(self, transcription_id: str, improved_text: str) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"improved_text": improved_text}},
        )

    async def set_structured_content(self, transcription_id: str, content: dict) -> None:
        await self.collection.update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"structured_content": content}},
        )
