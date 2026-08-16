import logging
import uuid

from qdrant_client.http.models import PointStruct
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database_models import Document
from app.services.chunking import split_text
from app.services.embeddings import embed_texts
from app.vector.qdrant_client import qdrant_client

logger = logging.getLogger(__name__)


def create_document(db: Session, source: str, text: str) -> Document:
    document = Document(source=source, text=text, status="idle")
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def claim_one_idle(db: Session) -> Document | None:
    document = (
        db.query(Document)
        .filter(Document.status == "idle")
        .order_by(Document.created_at)
        .with_for_update(skip_locked=True)
        .first()
    )
    if document is None:
        return None

    document.status = "syncing"
    db.commit()
    db.refresh(document)
    return document


def mark_indexed(db: Session, document: Document) -> None:
    document.status = "indexed"
    document.error = None
    db.commit()
    db.refresh(document)


def mark_failed_or_retry(db: Session, document: Document, error_msg: str) -> None:
    document.attempts += 1
    document.error = error_msg
    if document.attempts >= settings.MAX_ATTEMPTS:
        document.status = "failed"
    else:
        document.status = "idle"
    db.commit()
    db.refresh(document)


def index_document(db: Session, document: Document) -> None:
    document.status = "syncing"
    db.commit()
    db.refresh(document)

    try:
        chunks = split_text(
            document.text or "",
            settings.CHUNK_SIZE,
            settings.CHUNK_OVERLAP,
        )
        vectors = embed_texts(chunks)

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk,
                    "source": document.source,
                    "doc_id": document.id,
                    "section": section,
                },
            )
            for section, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]

        if points:
            qdrant_client.upsert(
                collection_name=settings.COLLECTION,
                points=points,
            )

        mark_indexed(db, document)
        logger.info(
            "Document %s indexed: %s chunks from source=%s",
            document.id,
            len(points),
            document.source,
        )
    except Exception as e:
        mark_failed_or_retry(db, document, str(e))
        db.refresh(document)
        logger.warning(
            "Document %s indexing failed: syncing -> %s, error=%s",
            document.id,
            document.status,
            e,
        )
        raise
