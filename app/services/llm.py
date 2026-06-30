import json
from typing import Union

from openai import AsyncOpenAI

from app.logger import logger
from config.settings import settings

PROMPTS: dict[str, str] = {
    "correction": (
        "Tu es un correcteur de texte. Corrige la grammaire, l'orthographe et la ponctuation "
        "du texte suivant sans en changer le sens ni le style. Retourne uniquement le texte corrigé."
    ),
    "reformulation": (
        "Tu es un rédacteur professionnel. Réécris le texte suivant de façon plus fluide et "
        "professionnelle, en conservant le sens original. Retourne uniquement le texte reformulé."
    ),
    "résumé": (
        "Tu es un assistant. Résume le texte suivant en 2-3 phrases concises. "
        "Retourne uniquement le résumé."
    ),
    "structured_meeting": (
        "Tu es un assistant de compte-rendu de réunion professionnel. "
        "Analyse cette transcription et retourne UNIQUEMENT un objet JSON valide (sans markdown, "
        "sans bloc ```json) avec exactement ces champs : "
        "titre (string — titre ou objectif principal de la réunion, inféré du contenu), "
        "introduction (string — contexte, date si mentionnée, participants si mentionnés), "
        "points (array of strings — chaque point abordé, une phrase complète par élément), "
        "conclusion (string — décisions prises, actions à suivre, prochaines étapes)."
    ),
}


async def improve_text(text: str, mode: str) -> Union[str, dict]:
    system_prompt = PROMPTS.get(mode)
    if system_prompt is None:
        raise ValueError("Mode inconnu")

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    )

    raw_content = response.choices[0].message.content or ""

    if mode == "structured_meeting":
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError:
            raise ValueError("Réponse LLM non parseable")
        logger.info(f"LLM structured_meeting — {len(text)} caractères → JSON parsé")
        return parsed

    logger.info(f"LLM improve — mode={mode}, {len(text)} caractères → {len(raw_content)} caractères")
    return raw_content
