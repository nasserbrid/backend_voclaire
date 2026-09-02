import os

# Doit être exécuté avant tout import de config.settings (qui crée Settings() au chargement du module).
# pydantic-settings lève une ValidationError si ces champs requis sont absents.
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017/test")
os.environ.setdefault("JWT_SECRET", "a" * 128)
os.environ.setdefault("GOOGLE_ID_CLIENT_VOCLAIRE", "fake_google_client_id")
os.environ.setdefault("GOOGLE_SECRET_CLIENT_VOCLAIRE", "fake_google_client_secret")
# OPENAI_API_KEY a un défaut ("") dans Settings, mais ChatOpenAI() (chat_service.py, niveau module)
# traite une clé vide comme absente et lève OpenAIError à l'import — avant même la collecte des tests.
# Aucun appel réseau réel n'est fait en test (GenericFakeChatModel remplace _llm) : une valeur factice suffit.
os.environ.setdefault("OPENAI_API_KEY", "sk-fake-test-key-not-a-real-secret")
