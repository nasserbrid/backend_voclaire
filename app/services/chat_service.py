from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.schemas.chat import ChatMessage
from app.services.chatbot_kb import KB_TEXT
from config.settings import settings

# Instance module-level : un seul client HTTP/pool de connexions réutilisé entre les requêtes,
# pas de recréation à chaque appel de answer().
_llm = ChatOpenAI(
    model=settings.CHAT_MODEL,
    temperature=settings.CHAT_TEMPERATURE,
    max_tokens=settings.CHAT_MAX_TOKENS,
    api_key=settings.OPENAI_API_KEY,
    timeout=20,
    max_retries=2,
)


def build_system_prompt(user: dict) -> str:
    plan = user.get("plan", "free")
    return (
        "Tu es l'assistant d'onboarding de Voclaire, un SaaS de transcription audio (Speech-to-Text) "
        "avec post-traitement par intelligence artificielle.\n"
        "Ton rôle : aider les visiteurs et utilisateurs à comprendre le produit, ses fonctionnalités, "
        "ses limites et ses tarifs.\n\n"
        "Règles absolues :\n"
        "- Ne réponds QU'À PARTIR de la base de connaissance ci-dessous. N'invente JAMAIS une "
        "fonctionnalité, un tarif ou une limite qui n'y figure pas.\n"
        "- Si la réponse à la question de l'utilisateur ne se trouve pas dans la base de connaissance, "
        "dis-le clairement et invite l'utilisateur à contacter Voclaire via la page de contact plutôt "
        "que de deviner.\n"
        "- Réponds en français, de façon concise et directe.\n\n"
        f"L'utilisateur à qui tu réponds est actuellement sur le plan : {plan}. "
        f"Le quota mensuel de post-traitements LLM du plan Free est de {settings.LLM_FREE_MONTHLY_QUOTA} "
        "par mois.\n\n"
        "--- BASE DE CONNAISSANCE ---\n"
        f"{KB_TEXT}\n"
        "--- FIN ---"
    )


def _to_lc_history(history: list[ChatMessage]) -> list[BaseMessage]:
    recent_history = history[-settings.CHAT_MAX_HISTORY :]
    lc_messages: list[BaseMessage] = []
    for entry in recent_history:
        if entry.role == "user":
            lc_messages.append(HumanMessage(content=entry.content))
        else:
            lc_messages.append(AIMessage(content=entry.content))
    return lc_messages


async def answer(user: dict, message: str, history: list[ChatMessage]) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", build_system_prompt(user)),
            MessagesPlaceholder("history"),
            ("human", "{message}"),
        ]
    )
    chain = prompt | _llm | StrOutputParser()
    return await chain.ainvoke(
        {
            "history": _to_lc_history(history),
            "message": message,
        }
    )
