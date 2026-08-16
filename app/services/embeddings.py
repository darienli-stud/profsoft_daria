from app.ai.client import client
from app.core.config import settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    if settings.TEST_MODE:
        return [[0.0] * settings.EMBED_DIM for _ in texts]

    response = client.embeddings.create(
        model=settings.EMBED_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
