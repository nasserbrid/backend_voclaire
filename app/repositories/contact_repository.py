from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.contact import build_contact_document


class ContactRepository:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection = database["contacts"]

    async def create(
        self,
        user_id: str,
        email: str,
        subject: str,
        message: str,
    ) -> dict:
        document = build_contact_document(
            user_id=user_id,
            email=email,
            subject=subject,
            message=message,
        )
        result = await self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        document["id"] = str(result.inserted_id)
        return document
