import re

from app.ai.client import client
from app.core.config import settings
from app.services.retrieval import search

SYSTEM_PROMPT = (
    "Отвечай ТОЛЬКО на основе предоставленного контекста. "
    "Если в контексте нет ответа — прямо скажи, что в документации нет информации. "
    "В ответе укажи источник (source) для использованных фрагментов."
)

_STOPWORDS = {
    "что",
    "как",
    "где",
    "когда",
    "кто",
    "это",
    "для",
    "или",
    "при",
    "про",
    "есть",
    "ли",
    "на",
    "по",
    "из",
    "в",
    "и",
    "а",
    "с",
    "о",
    "об",
    "the",
    "a",
    "an",
    "is",
    "are",
    "to",
    "of",
    "in",
    "on",
    "for",
}


def answer(question: str) -> dict:
    points = search(question, settings.TOP_K)

    context_parts: list[str] = []
    sources: list[dict] = []
    for point in points:
        payload = point.payload or {}
        text = payload.get("text", "")
        source = payload.get("source")
        section = payload.get("section")
        context_parts.append(
            f"[source={source}, section={section}]\n{text}"
        )
        sources.append(
            {
                "source": source,
                "section": section,
                "score": point.score,
                "text": text,
            }
        )

    context = "\n\n".join(context_parts) if context_parts else "(контекст пуст)"

    if settings.TEST_MODE:
        if not context_parts or not _has_overlap(question, context):
            reply = "В документации нет информации по этому вопросу."
            return {"answer": reply, "sources": sources}
        reply = (
            f"Ответ на основе контекста (TEST_MODE): {context_parts[0][:300]} "
            f"(источник: {sources[0].get('source')})"
        )
        return {"answer": reply, "sources": sources}

    response = client.chat.completions.create(
        model=settings.CHAT_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Контекст:\n{context}\n\nВопрос: {question}",
            },
        ],
    )
    reply = (response.choices[0].message.content or "").strip()
    return {"answer": reply, "sources": sources}


def _has_overlap(question: str, context: str) -> bool:
    q_tokens = {
        t
        for t in re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]{3,}", question.lower())
        if t not in _STOPWORDS
    }
    if not q_tokens:
        return False
    context_l = context.lower()
    return any(token in context_l for token in q_tokens)
