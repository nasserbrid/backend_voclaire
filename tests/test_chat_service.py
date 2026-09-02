from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.schemas.chat import ChatMessage
from app.services import chat_service
from config.settings import settings

USER_FREE = {"_id": "user_free", "email": "free@example.com", "plan": "free"}
USER_PRO = {"_id": "user_pro", "email": "pro@example.com", "plan": "pro"}


def test_build_system_prompt_contains_kb_extract() -> None:
    """Le system prompt embarque bien la base de connaissance (pas de RAG en v1)."""
    prompt = chat_service.build_system_prompt(USER_FREE)

    assert "Whisper" in prompt
    assert "diarisation" in prompt.lower() or "intervenant" in prompt.lower()


def test_build_system_prompt_contains_free_quota() -> None:
    """Le quota mensuel Free (settings.LLM_FREE_MONTHLY_QUOTA) est injecté dans le prompt."""
    prompt = chat_service.build_system_prompt(USER_FREE)

    assert str(settings.LLM_FREE_MONTHLY_QUOTA) in prompt


def test_build_system_prompt_reflects_user_plan() -> None:
    """Le plan de l'utilisateur (free vs pro) apparaît distinctement dans le prompt."""
    prompt_free = chat_service.build_system_prompt(USER_FREE)
    prompt_pro = chat_service.build_system_prompt(USER_PRO)

    assert "plan : free" in prompt_free
    assert "plan : pro" in prompt_pro
    assert prompt_free != prompt_pro


def test_to_lc_history_keeps_last_n_messages_in_order() -> None:
    """Un historique de 60 messages est tronqué aux CHAT_MAX_HISTORY derniers, dans l'ordre."""
    history = [
        ChatMessage(role="user" if i % 2 == 0 else "assistant", content=f"message-{i}")
        for i in range(60)
    ]

    lc_history = chat_service._to_lc_history(history)

    assert len(lc_history) == settings.CHAT_MAX_HISTORY
    expected_contents = [entry.content for entry in history[-settings.CHAT_MAX_HISTORY :]]
    actual_contents = [message.content for message in lc_history]
    assert actual_contents == expected_contents


async def test_answer_invokes_chain_without_network_call() -> None:
    """answer() traverse toute la chaîne LCEL (prompt | llm | parser) avec un faux modèle — zéro appel réseau."""
    fake_llm = GenericFakeChatModel(messages=iter([AIMessage(content="Réponse simulée par le faux modèle.")]))

    with patch.object(chat_service, "_llm", fake_llm):
        reply = await chat_service.answer(user=USER_FREE, message="Bonjour", history=[])

    assert reply == "Réponse simulée par le faux modèle."
