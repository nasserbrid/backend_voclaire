import os

# Doit être exécuté avant tout import de config.settings (qui crée Settings() au chargement du module).
# pydantic-settings lève une ValidationError si ces champs requis sont absents.
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("JWT_SECRET", "a" * 128)
os.environ.setdefault("GOOGLE_ID_CLIENT_VOCLAIRE", "fake_google_client_id")
os.environ.setdefault("GOOGLE_SECRET_CLIENT_VOCLAIRE", "fake_google_client_secret")
