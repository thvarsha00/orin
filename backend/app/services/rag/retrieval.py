"""Question -> embedding -> similarity search -> ranked passages with real document/page metadata."""
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, DocumentChunk
from app.services.rag import embeddings, vector_store

logger = logging.getLogger("orin.rag")


@dataclass
class Passage:
    document_id: int
    document_name: str
    page_number: int | None
    chunk_index: int
    text: str
    score: float


async def retrieve(db: Session, user_id: int, question: str, document_ids: list[int] | None,
                   top_k: int | None = None) -> list[Passage]:
    """Only passages scoring at least RAG_MIN_SCORE are returned; an empty list means 'not in your materials'."""
    query = (await embeddings.embed_texts([question]))[0]
    hits = vector_store.search(db, user_id, query, embeddings.model_name(), document_ids,
                               top_k or settings.rag_top_k)
    best = hits[0].score if hits else None
    hits = [h for h in hits if h.score >= settings.rag_min_score]
    # Logged so RAG_MIN_SCORE can be tuned against the real embedding model.
    logger.info("RAG retrieve: best score %s, %d passage(s) >= %.2f", f"{best:.3f}" if best is not None else "n/a",
                len(hits), settings.rag_min_score)
    if not hits:
        return []
    texts = dict(db.execute(select(DocumentChunk.id, DocumentChunk.text)
                            .where(DocumentChunk.id.in_([h.chunk_id for h in hits]))).all())
    names = dict(db.execute(select(Document.id, Document.filename)
                            .where(Document.id.in_({h.document_id for h in hits}))).all())
    return [Passage(h.document_id, names[h.document_id], h.page_number, h.chunk_index, texts[h.chunk_id], h.score)
            for h in hits]
