import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Document, User
from app.schemas.documents import AllDocumentsChatIn, DocumentChatIn, DocumentOut
from app.services.ai import AIError, get_ai
from app.services.language import build_system_prompt, resolve_profile
from app.services.rag import answer, embeddings, storage
from app.services.rag.ingestion import IN_PROGRESS, process_document
from app.services.rag.retrieval import retrieve

logger = logging.getLogger("orin.documents")
router = APIRouter(prefix="/api/documents", tags=["documents"])
HISTORY_LIMIT = 6
MEDIA = {"pdf": "application/pdf", "txt": "text/plain; charset=utf-8", "md": "text/plain; charset=utf-8"}


def _owned(db: Session, user: User, document_id: int) -> Document:
    """404 (not 403) for other people's documents, so ids of other users' files are never confirmed."""
    doc = db.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(404, "Document not found.")
    return doc


def _ndjson(event: dict) -> bytes:
    return (json.dumps(event, ensure_ascii=False) + "\n").encode()


# ---- library --------------------------------------------------------------------------------
@router.get("/config")
async def config(_: User = Depends(get_current_user)):
    """Limits for the upload UI plus whether the embedding model is ready (uploads cannot finish without it)."""
    return {"max_mb": settings.max_doc_mb, "types": sorted(storage.TYPES), "embedding": await embeddings.status()}


@router.get("", response_model=list[DocumentOut])
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Document).where(Document.user_id == user.id).order_by(Document.id.desc())))


@router.post("", response_model=DocumentOut, status_code=202)
async def upload(request: Request, background: BackgroundTasks, file: UploadFile = File(...),
                 user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    limit = storage.max_bytes()
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit + 512 * 1024:
        raise HTTPException(413, f"That file is too large. The limit is {settings.max_doc_mb:g} MB.")
    data = await file.read(limit + 1)
    if not data:
        raise HTTPException(400, "The file is empty. Please choose another one.")
    if len(data) > limit:
        raise HTTPException(413, f"That file is too large. The limit is {settings.max_doc_mb:g} MB.")
    name = storage.display_name(file.filename)
    file_type = storage.sniff_type(name, data)
    if not file_type:
        raise HTTPException(415, "Unsupported file. Please upload a PDF (or a .txt / .md notes file).")

    path = storage.save(user.id, data, file_type)
    try:
        doc = Document(user_id=user.id, filename=name, file_type=file_type, file_path=path,
                       file_size=len(data), status="queued")
        db.add(doc)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(path)
        raise
    background.add_task(process_document, doc.id)
    return doc


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned(db, user, document_id)


@router.post("/{document_id}/retry", response_model=DocumentOut, status_code=202)
def retry(document_id: int, background: BackgroundTasks, user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    doc = _owned(db, user, document_id)
    if doc.status in IN_PROGRESS:
        raise HTTPException(409, "This document is already being processed.")
    doc.status, doc.error = "queued", None
    db.commit()
    background.add_task(process_document, doc.id)
    return doc


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _owned(db, user, document_id)
    path = doc.file_path
    db.delete(doc)   # chunks and their vectors are removed with it (cascade)
    db.commit()
    storage.delete(path)


@router.get("/{document_id}/file")
def document_file(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The original upload, for 'View source'. Only ever served to its owner."""
    doc = _owned(db, user, document_id)
    path = storage.resolve(doc.file_path)
    if not path or not path.is_file():
        raise HTTPException(404, "This file is no longer available.")
    return FileResponse(path, media_type=MEDIA[doc.file_type], content_disposition_type="inline",
                        filename=doc.filename if doc.file_type != "pdf" else None,
                        headers={"Cache-Control": "private, max-age=600", "X-Content-Type-Options": "nosniff"})


# ---- grounded chat --------------------------------------------------------------------------
async def _grounded_reply(db: Session, user: User, data: DocumentChatIn, docs: list[Document]) -> StreamingResponse:
    current = embeddings.model_name()
    usable = [d for d in docs if d.embed_model == current]
    if docs and not usable:
        raise HTTPException(409, "These documents were processed with a different embedding model. "
                                 "Open the Documents page and retry processing.")
    ids = [d.id for d in usable]
    top_k = settings.rag_top_k * (2 if len(ids) > 1 else 1)
    passages = await retrieve(db, user.id, data.question, ids, top_k)

    async def not_found() -> AsyncIterator[bytes]:
        yield _ndjson({"type": "sources", "sources": []})
        yield _ndjson({"type": "token", "text": answer.NOT_FOUND})
        yield _ndjson({"type": "done"})

    headers = {"Cache-Control": "no-store"}
    if not passages:
        return StreamingResponse(not_found(), media_type="application/x-ndjson", headers=headers)

    prefs = user.profile
    script_pref = data.script if data.script != "auto" else prefs.preferred_script
    profile, _ = resolve_profile(data.language, data.question, script_pref, prefs.last_detected_script)
    system = build_system_prompt("rag", profile, data.level, extra=answer.RAG_RULES)
    history = [{"role": t.role, "content": t.content} for t in data.history[-HISTORY_LIMIT:]]
    stream = get_ai().stream([{"role": "system", "content": system}, *history,
                              {"role": "user", "content": answer.user_turn(data.question, passages)}])
    try:  # surface provider errors as a proper HTTP error before any bytes are sent
        first = await anext(stream)
    except StopAsyncIteration:
        first = ""
    except AIError as e:
        raise HTTPException(e.status_code, e.message)

    async def body() -> AsyncIterator[bytes]:
        yield _ndjson({"type": "sources", "sources": answer.source_payload(passages)})
        if first:
            yield _ndjson({"type": "token", "text": first})
        try:
            async for chunk in stream:
                yield _ndjson({"type": "token", "text": chunk})
        except AIError as e:
            yield _ndjson({"type": "error", "message": e.message})
            return
        yield _ndjson({"type": "done"})

    return StreamingResponse(body(), media_type="application/x-ndjson", headers=headers)


def _require_ready(doc: Document) -> None:
    if doc.status == "failed":
        raise HTTPException(409, "This document could not be processed. Retry it from the Documents page.")
    if doc.status != "ready":
        raise HTTPException(409, "This document is still being processed. Try again in a moment.")


@router.post("/chat")
async def chat_all(data: AllDocumentsChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Ask across the student's documents (all ready ones, or the ids given)."""
    if data.document_ids:
        docs = [_owned(db, user, i) for i in dict.fromkeys(data.document_ids)]
        docs = [d for d in docs if d.status == "ready"]
    else:
        docs = list(db.scalars(select(Document).where(Document.user_id == user.id, Document.status == "ready")))
    if not docs:
        raise HTTPException(409, answer.NO_READY_DOCS)
    return await _grounded_reply(db, user, data, docs)


@router.post("/{document_id}/chat")
async def chat_one(document_id: int, data: DocumentChatIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    doc = _owned(db, user, document_id)
    _require_ready(doc)
    return await _grounded_reply(db, user, data, [doc])
