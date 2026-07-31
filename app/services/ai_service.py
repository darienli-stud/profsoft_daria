from app.ai.client import client
from app.core.config import settings

_VALID_LABELS = {"positive", "negative", "neutral"}


def classify(text: str) -> str:
    if settings.TEST_MODE:
        return "neutral"

    response = client.chat.completions.create(
        model=settings.MODEL,
        messages=[
            {"role": "system", "content": settings.PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content.strip().lower()
    if content not in _VALID_LABELS:
        return "neutral"
    return content
