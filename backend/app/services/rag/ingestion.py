"""Ingestion pipeline: stored file -> pages -> chunks -> embeddings -> rows. Runs in the background after upload
and again on retry. Progress is the document's `status`, which the UI polls."""
import asyncio
import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Document, DocumentChunk
from app.services.ai.base import AIError
from app.services.rag import embeddings, storage, vector_store
from app.services.rag.chunking import chunk_pages
from app.services.rag.extraction import ExtractionError, extract

logger = logging.getLogger("orin.rag")
IN_PROGRESS = ("queued", "extracting", "embedding")


def _exists(db: Session, document_id: int) -> bool:
    """Asks the database (db.get would answer from the session cache even after another request deleted the row)."""
    return db.scalar(select(Document.id).where(Document.id == document_id)) is not None


def _set(db: Session, doc: Document, **fields) -> None:
    for key, value in fields.items():
        setattr(doc, key, value)
    db.commit()


async def process_document(document_id: int, session_factory=SessionLocal) -> None:
    """Never raises: any failure becomes status='failed' with a message the student can act on."""
    db = session_factory()
    try:
        doc = db.get(Document, document_id)
        if not doc:  # deleted before processing started
            return
        try:
            await _run(db, doc)
        except ExtractionError as e:
            _fail(db, doc, e.message)
        except AIError as e:
            _fail(db, doc, e.message)
        except Exception:
            logger.exception("Document %s failed during processing", document_id)
            db.rollback()
            _fail(db, doc, "Something went wrong while processing this document. Please retry.")
    finally:
        db.close()


def _fail(db: Session, doc: Document, message: str) -> None:
    db.rollback()
    if _exists(db, doc.id):  # it may have been deleted mid-run
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))
        _set(db, doc, status="failed", error=message, chunk_count=0)


async def _run(db: Session, doc: Document) -> None:
    data = storage.read(doc.file_path)
    if data is None:
        raise ExtractionError("The uploaded file is no longer available. Please upload it again.")

    _set(db, doc, status="extracting", error=None)
    extracted = await asyncio.to_thread(extract, data, doc.file_type)
    chunks = chunk_pages(extracted.pages)
    if not chunks:
        raise ExtractionError("No readable text was found in this document.")

    _set(db, doc, status="embedding", page_count=extracted.page_count)
    vectors = await embeddings.embed_texts([c.text for c in chunks])

    if not _exists(db, doc.id):  # deleted while embedding: store nothing
        return
    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc.id))  # retry starts clean
    db.add_all(DocumentChunk(document_id=doc.id, chunk_index=c.index, page_number=c.page_number, text=c.text,
                             embedding=vector_store.to_blob(vectors[i])) for i, c in enumerate(chunks))
    _set(db, doc, status="ready", chunk_count=len(chunks), embed_model=embeddings.model_name(), error=None)


def recover_interrupted() -> None:
    """A restart kills background jobs; mark those documents failed so the UI offers Retry instead of spinning."""
    with SessionLocal() as db:
        stuck = db.query(Document).filter(Document.status.in_(IN_PROGRESS)).all()
        for doc in stuck:
            doc.status, doc.error = "failed", "Processing was interrupted. Please retry."
        db.commit()
