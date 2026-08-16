from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings

qdrant_client = QdrantClient(url=settings.QDRANT_URL)


def ensure_collection() -> None:
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if settings.COLLECTION not in collections:
        qdrant_client.create_collection(
            collection_name=settings.COLLECTION,
            vectors_config=VectorParams(
                size=settings.EMBED_DIM,
                distance=Distance.COSINE,
            ),
        )
