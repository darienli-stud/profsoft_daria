from app.core.config import settings
from app.services.embeddings import embed_texts
from app.vector.qdrant_client import qdrant_client


def search(question: str, k: int) -> list:
    vectors = embed_texts([question])
    if not vectors:
        return []

    result = qdrant_client.query_points(
        collection_name=settings.COLLECTION,
        query=vectors[0],
        limit=k,
        with_payload=True,
    )
    return list(result.points)
