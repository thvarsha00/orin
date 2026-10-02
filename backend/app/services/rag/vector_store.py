"""Vector storage: L2-normalised float32 vectors live in the `document_chunks.embedding` column and are searched
with brute-force cosine similarity (numpy). Right-sized for a student's own library (thousands of chunks), needs
no extra server, and deleting a document deletes its vectors in the same transaction."""
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk


@dataclass
class Hit:
    chunk_id: int
    document_id: int
    page_number: int | None
    chunk_index: int
    score: float


def to_blob(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


def search(db: Session, user_id: int, query: np.ndarray, embed_model: str, document_ids: list[int] | None,
           top_k: int) -> list[Hit]:
    """Top-k chunks by cosine similarity. Always scoped to `user_id`, whatever ids the caller passes, and only
    to ready documents embedded with the current model (vectors from different models are not comparable)."""
    q = select(DocumentChunk.id, DocumentChunk.document_id, DocumentChunk.page_number,
               DocumentChunk.chunk_index, DocumentChunk.embedding) \
        .join(Document, Document.id == DocumentChunk.document_id) \
        .where(Document.user_id == user_id, Document.status == "ready", Document.embed_model == embed_model,
               DocumentChunk.embedding.is_not(None))
    if document_ids is not None:
        q = q.where(Document.id.in_(document_ids))
    rows = [r for r in db.execute(q) if len(r.embedding) == query.size * 4]  # skip vectors of another dimension
    if not rows:
        return []
    matrix = np.vstack([from_blob(r.embedding) for r in rows])
    scores = matrix @ query.astype(np.float32)
    best = np.argsort(-scores)[:top_k]
    return [Hit(rows[i].id, rows[i].document_id, rows[i].page_number, rows[i].chunk_index, float(scores[i]))
            for i in best]
