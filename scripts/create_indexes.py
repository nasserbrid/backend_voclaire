"""
Script à exécuter une seule fois pour créer les index MongoDB.
Idempotent : peut être relancé sans risque si les index existent déjà.

Lancer depuis backend_voclaire/ :
    python scripts/create_indexes.py
"""

import asyncio
import sys
from pathlib import Path

# Permettre l'import de config/ depuis ce script
sys.path.append(str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient

from config.settings import settings


async def create_indexes() -> None:
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client["voclaire"]
    users_collection = db["users"]
    transcriptions_collection = db["transcriptions"]

    # Index unique sur email — chaque adresse email ne peut apparaître qu'une fois
    await users_collection.create_index("email", unique=True)
    print("✓ Index créé : users.email (unique)")

    # Index unique + sparse sur google_id
    # sparse=True : les documents sans ce champ (users formulaire) sont ignorés par l'index
    # Sans sparse, MongoDB indexerait les null et bloquerait les insertions après le premier user sans google_id
    await users_collection.create_index("google_id", unique=True, sparse=True)
    print("✓ Index créé : users.google_id (unique, sparse)")

    # Index sur user_id pour les requêtes find_by_user_id (GET /transcriptions)
    await transcriptions_collection.create_index("user_id")
    print("✓ Index créé : transcriptions.user_id")

    # Index sur created_at pour le tri anti-chronologique (déjà utilisé avec sort)
    await transcriptions_collection.create_index([("user_id", 1), ("created_at", -1)])
    print("✓ Index créé : transcriptions.(user_id, created_at) composé")

    client.close()
    print("\nIndex MongoDB initialisés avec succès.")


if __name__ == "__main__":
    asyncio.run(create_indexes())
