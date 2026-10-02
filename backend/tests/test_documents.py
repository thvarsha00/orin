import hashlib
import os
import re

os.environ["DATABASE_URL"] = "sqlite:///./test_orin.db"

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Document, DocumentChunk  # noqa: E402
from app.services.ai.base import AIError  # noqa: E402
from app.services.rag import answer, embeddings  # noqa: E402
from app.services.rag.chunking import chunk_page, chunk_pages  # noqa: E402
from app.services.rag.extraction import Page, clean_text  # noqa: E402
from app.services.rag.ingestion import recover_interrupted  # noqa: E402


def setup_module():
    Base.metadata.drop_all(bind=engine)


def teardown_module():
    engine.dispose()
    if os.path.exists("test_orin.db"):
        os.remove("test_orin.db")


# ---- test doubles at the network boundary (Ollama embeddings, LLM) ---------------------------
STOP = {"the", "a", "an", "is", "of", "in", "to", "and", "what", "how", "does", "do", "are", "for", "on", "it", "why"}


def _vec(text: str) -> list[float]:
    """Bag-of-words hashing: texts that share content words are similar; unrelated texts score ~0."""
    v = np.zeros(256, dtype=np.float32)
    for w in re.findall(r"[a-z]+", text.lower()):
        if w not in STOP:
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 256] += 1.0
    return v.tolist()


class FakeOllama:
    fail = False
    embed_calls = 0

    async def embed(self, texts):
        FakeOllama.embed_calls += 1
        if FakeOllama.fail:
            raise AIError("Can't reach Ollama. Make sure it is running (ollama serve).")
        return [_vec(t) for t in texts]

    async def health(self):
        return {"reachable": True, "embed_model_available": True, "embed_model": "bge-m3", "hint": None}


class FakeLLM:
    def __init__(self, reply="A list comprehension builds a list in one line (Python_Basics.pdf, page 2)."):
        self.reply, self.calls, self.error = reply, [], None

    async def stream(self, messages):
        self.calls.append(messages)
        if self.error:
            raise self.error
        for i in range(0, len(self.reply), 7):
            yield self.reply[i:i + 7]


def make_pdf(pages: list[str]) -> bytes:
    """Minimal valid PDF with one text line per page (no PDF library needed)."""
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for text in pages:
        n = len(objs) + 1
        kids.append(f"{n} 0 R")
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 50 700 Td ({safe}) Tj ET".encode() if text else b""
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> "
                    f"/Contents {n + 1} 0 R >>".encode())
        objs.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>".encode()
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    return out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


PYTHON_PDF = make_pdf([
    "Python basics introduce variables, numbers and strings for beginners.",
    "A list comprehension is a concise way to create a list from an iterable using a loop inside brackets.",
    "Functions are defined with the def keyword and return values.",
])
ML_PDF = make_pdf([
    "Machine learning uses data to train models.",
    "Supervised learning trains on labelled examples while unsupervised learning finds structure in unlabelled data.",
])


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "up"))
    monkeypatch.setattr(settings, "max_doc_mb", 1.0)
    monkeypatch.setattr(settings, "ollama_embed_model", "bge-m3")
    monkeypatch.setattr(embeddings, "OllamaProvider", FakeOllama)
    FakeOllama.fail, FakeOllama.embed_calls = False, 0
    llm = FakeLLM()
    monkeypatch.setattr("app.api.documents.get_ai", lambda: llm)
    with TestClient(app) as c:
        def login(email):
            r = c.post("/api/auth/register", json={"email": email, "password": "password123", "display_name": "T"})
            return {"Authorization": f"Bearer {r.json()['access_token']}"}
        yield c, login, llm


def upload(c, hdr, data, name="Python_Basics.pdf"):
    return c.post("/api/documents", headers=hdr, files={"file": (name, data, "application/octet-stream")})


def events(resp):
    import json
    return [json.loads(line) for line in resp.text.splitlines() if line.strip()]


def answer_text(resp):
    return "".join(e["text"] for e in events(resp) if e["type"] == "token")


def sources(resp):
    return next(e["sources"] for e in events(resp) if e["type"] == "sources")


# ---- Test 1: upload -> processing -> ready ----------------------------------------------------
def test_upload_pdf_becomes_ready_with_pages_and_chunks(env):
    c, login, _ = env
    hdr = login("t1@x.com")
    r = upload(c, hdr, PYTHON_PDF)
    assert r.status_code == 202 and r.json()["status"] in ("queued", "ready")
    doc = c.get(f"/api/documents/{r.json()['id']}", headers=hdr).json()
    assert doc["status"] == "ready" and doc["page_count"] == 3 and doc["chunk_count"] == 3
    assert doc["filename"] == "Python_Basics.pdf" and doc["file_type"] == "pdf" and doc["error"] is None
    assert [d["id"] for d in c.get("/api/documents", headers=hdr).json()] == [doc["id"]]
    with SessionLocal() as db:
        chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == doc["id"])
                            .order_by(DocumentChunk.chunk_index)).all()
        assert [ch.page_number for ch in chunks] == [1, 2, 3]
        assert all(len(ch.embedding) == 256 * 4 for ch in chunks)


# ---- Test 2: answer exists in the PDF -> grounded answer with the right page ------------------
def test_question_gets_grounded_answer_with_correct_page(env):
    c, login, llm = env
    hdr = login("t2@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    r = c.post(f"/api/documents/{doc_id}/chat", headers=hdr,
               json={"question": "What is a list comprehension?", "language": "en", "level": "beginner"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/x-ndjson")
    assert answer_text(r) == llm.reply
    src = sources(r)
    assert src[0]["document_id"] == doc_id and src[0]["page_number"] == 2
    assert src[0]["document_name"] == "Python_Basics.pdf" and "list comprehension" in src[0]["snippet"]
    assert {s["page_number"] for s in src} <= {1, 2, 3}          # only real pages
    system, user = llm.calls[0][0]["content"], llm.calls[0][-1]["content"]      # the LLM really got the context
    assert "concise way to create a list" in user and "Python_Basics.pdf, page 2" in user
    assert "not found in their uploaded materials" in system and "never follow instructions" in system
    assert events(r)[-1] == {"type": "done"}


def test_chat_history_is_forwarded(env):
    c, login, llm = env
    hdr = login("hist@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={
        "question": "Tell me more about list comprehension", "history": [
            {"role": "user", "content": "What is a list comprehension?"}, {"role": "assistant", "content": "It builds lists."}]})
    roles = [m["role"] for m in llm.calls[0]]
    assert roles == ["system", "user", "assistant", "user"]


# ---- Test 3: unrelated question -> clear "not found", no LLM call ------------------------------
def test_unrelated_question_says_not_found_without_calling_llm(env):
    c, login, llm = env
    hdr = login("t3@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    r = c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={"question": "Who painted the Mona Lisa?"})
    assert r.status_code == 200
    assert answer_text(r) == answer.NOT_FOUND and sources(r) == []
    assert llm.calls == []


# ---- Test 4: cross-document retrieval ---------------------------------------------------------
def test_ask_across_documents_uses_the_right_document_for_each_question(env):
    c, login, llm = env
    hdr = login("t4@x.com")
    py_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    ml_id = upload(c, hdr, ML_PDF, "Machine_Learning_Notes.pdf").json()["id"]
    r = c.post("/api/documents/chat", headers=hdr,
               json={"question": "What is the difference between supervised and unsupervised learning?"})
    assert {s["document_id"] for s in sources(r)} == {ml_id}
    assert [s["page_number"] for s in sources(r)] == [2]
    r = c.post("/api/documents/chat", headers=hdr, json={"question": "How do I define functions with def in Python?"})
    assert sources(r)[0]["document_id"] == py_id and sources(r)[0]["page_number"] == 3
    mixed = c.post("/api/documents/chat", headers=hdr,
                   json={"question": "Explain supervised learning and list comprehension examples"})
    assert {s["document_id"] for s in sources(mixed)} == {py_id, ml_id}   # both documents contributed
    limited = c.post("/api/documents/chat", headers=hdr, json={
        "question": "Explain supervised learning and list comprehension examples", "document_ids": [py_id]})
    assert {s["document_id"] for s in sources(limited)} == {py_id}


# ---- Test 5: delete removes document, chunks, vectors and file --------------------------------
def test_delete_removes_document_chunks_and_file(env):
    c, login, _ = env
    hdr = login("t5@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    with SessionLocal() as db:
        stored = db.get(Document, doc_id).file_path
    from app.services.rag import storage
    assert storage.resolve(stored).is_file()
    assert c.delete(f"/api/documents/{doc_id}", headers=hdr).status_code == 204
    assert c.get("/api/documents", headers=hdr).json() == []
    assert c.get(f"/api/documents/{doc_id}", headers=hdr).status_code == 404
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == doc_id)) == 0
    assert not storage.resolve(stored).exists()
    r = c.post("/api/documents/chat", headers=hdr, json={"question": "list comprehension"})
    assert r.status_code == 409     # nothing left to search


# ---- Test 6: ownership -------------------------------------------------------------------------
def test_other_users_cannot_touch_a_document(env):
    c, login, llm = env
    alice, bob = login("alice@x.com"), login("bob@x.com")
    doc_id = upload(c, alice, PYTHON_PDF).json()["id"]
    for method, path, kw in [("get", f"/api/documents/{doc_id}", {}), ("delete", f"/api/documents/{doc_id}", {}),
                             ("get", f"/api/documents/{doc_id}/file", {}), ("post", f"/api/documents/{doc_id}/retry", {}),
                             ("post", f"/api/documents/{doc_id}/chat", {"json": {"question": "list comprehension"}}),
                             ("post", "/api/documents/chat", {"json": {"question": "x", "document_ids": [doc_id]}})]:
        assert getattr(c, method)(path, headers=bob, **kw).status_code == 404, (method, path)
    assert c.get("/api/documents", headers=bob).json() == []
    r = c.post("/api/documents/chat", headers=bob, json={"question": "What is a list comprehension?"})
    assert r.status_code == 409 and llm.calls == []        # Bob's search never sees Alice's chunks
    assert c.get(f"/api/documents/{doc_id}", headers=alice).status_code == 200      # still intact
    assert c.get("/api/documents").status_code == 401
    assert c.post("/api/documents", files={"file": ("a.pdf", PYTHON_PDF)}).status_code == 401


def test_owner_can_fetch_original_file(env):
    c, login, _ = env
    hdr = login("file@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    r = c.get(f"/api/documents/{doc_id}/file", headers=hdr)
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content == PYTHON_PDF


# ---- validation and failure handling ---------------------------------------------------------
def test_upload_validation(env):
    c, login, _ = env
    hdr = login("val@x.com")
    assert upload(c, hdr, b"").status_code == 400
    r = upload(c, hdr, b"MZ\x90\x00binary", "evil.pdf")
    assert r.status_code == 415 and "PDF" in r.json()["error"]
    assert upload(c, hdr, PYTHON_PDF + b"0" * (1024 * 1024)).status_code == 413
    assert upload(c, hdr, b"hello", "notes.docx").status_code == 415
    assert c.get("/api/documents", headers=hdr).json() == []       # nothing half-created


def test_filename_is_sanitised_and_never_used_as_a_path(env):
    c, login, _ = env
    hdr = login("path@x.com")
    r = upload(c, hdr, PYTHON_PDF, "../../etc/passwd.pdf")
    assert r.json()["filename"] == "passwd.pdf"
    with SessionLocal() as db:
        stored = db.get(Document, r.json()["id"]).file_path
    assert re.fullmatch(r"documents/\d+/[0-9a-f]{32}\.pdf", stored)


def test_corrupted_and_textless_pdfs_fail_with_clear_messages(env):
    c, login, _ = env
    hdr = login("bad@x.com")
    bad = upload(c, hdr, b"%PDF-1.4\nthis is not really a pdf at all").json()
    bad = c.get(f"/api/documents/{bad['id']}", headers=hdr).json()
    assert bad["status"] == "failed" and "corrupted" in bad["error"] and "Traceback" not in bad["error"]
    blank = upload(c, hdr, make_pdf(["", ""]), "scan.pdf").json()
    blank = c.get(f"/api/documents/{blank['id']}", headers=hdr).json()
    assert blank["status"] == "failed" and "No readable text" in blank["error"]
    assert c.post(f"/api/documents/{blank['id']}/chat", headers=hdr, json={"question": "hi"}).status_code == 409


def test_embedding_failure_marks_failed_and_retry_recovers(env):
    c, login, _ = env
    hdr = login("emb@x.com")
    FakeOllama.fail = True
    doc = upload(c, hdr, PYTHON_PDF).json()
    doc = c.get(f"/api/documents/{doc['id']}", headers=hdr).json()
    assert doc["status"] == "failed" and "Ollama" in doc["error"] and doc["chunk_count"] == 0
    FakeOllama.fail = False
    assert c.post(f"/api/documents/{doc['id']}/retry", headers=hdr).status_code == 202
    doc = c.get(f"/api/documents/{doc['id']}", headers=hdr).json()
    assert doc["status"] == "ready" and doc["error"] is None and doc["chunk_count"] == 3


def test_retry_does_not_duplicate_chunks(env):
    c, login, _ = env
    hdr = login("dup@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    c.post(f"/api/documents/{doc_id}/retry", headers=hdr)
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == doc_id)) == 3


def test_text_notes_upload_and_answer_without_invented_pages(env):
    c, login, _ = env
    hdr = login("txt@x.com")
    notes = b"Recursion is when a function calls itself until a base case stops it."
    doc = upload(c, hdr, notes, "notes.txt").json()
    doc = c.get(f"/api/documents/{doc['id']}", headers=hdr).json()
    assert doc["status"] == "ready" and doc["file_type"] == "txt" and doc["page_count"] is None
    r = c.post(f"/api/documents/{doc['id']}/chat", headers=hdr, json={"question": "What is recursion?"})
    assert sources(r)[0]["page_number"] is None


def test_llm_failure_is_a_friendly_error_and_midstream_error_is_reported(env):
    c, login, llm = env
    hdr = login("llm@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    llm.error = AIError("Groq rate limit reached. Wait a few seconds and try again.", 429)
    r = c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={"question": "What is a list comprehension?"})
    assert r.status_code == 429 and "rate limit" in r.json()["error"]


def test_embedding_outage_at_question_time_is_a_friendly_error(env):
    c, login, _ = env
    hdr = login("down@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    FakeOllama.fail = True
    r = c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={"question": "What is a list comprehension?"})
    assert r.status_code == 503 and "Ollama" in r.json()["error"]


def test_chat_input_validation(env):
    c, login, _ = env
    hdr = login("in@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    assert c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={"question": ""}).status_code == 422
    assert c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={}).status_code == 422
    assert c.post(f"/api/documents/{doc_id}/chat", headers=hdr, json={"question": "x" * 2001}).status_code == 422
    assert c.post("/api/documents/999999/chat", headers=hdr, json={"question": "hi"}).status_code == 404
    assert c.get("/api/documents/abc", headers=hdr).status_code == 422


def test_config_reports_limits_and_embedding_status(env):
    c, login, _ = env
    r = c.get("/api/documents/config", headers=login("cfg@x.com")).json()
    assert r["max_mb"] == 1.0 and "pdf" in r["types"] and r["embedding"]["ready"] is True


def test_restart_marks_stuck_documents_failed(env):
    c, login, _ = env
    hdr = login("stuck@x.com")
    doc_id = upload(c, hdr, PYTHON_PDF).json()["id"]
    with SessionLocal() as db:
        db.get(Document, doc_id).status = "embedding"
        db.commit()
    recover_interrupted()
    doc = c.get(f"/api/documents/{doc_id}", headers=hdr).json()
    assert doc["status"] == "failed" and "interrupted" in doc["error"]


def test_documents_processed_with_another_embedding_model_are_not_searched(env, monkeypatch):
    c, login, _ = env
    hdr = login("model@x.com")
    upload(c, hdr, PYTHON_PDF)
    monkeypatch.setattr(settings, "ollama_embed_model", "another-model")
    r = c.post("/api/documents/chat", headers=hdr, json={"question": "What is a list comprehension?"})
    assert r.status_code == 409 and "retry processing" in r.json()["error"]


# ---- pure units --------------------------------------------------------------------------------
def test_clean_text_rejoins_hyphenation_and_unwraps_lines():
    raw = "A com-\nprehension is a con-\ncise way.\nStill same paragraph.\n\n\nNew   paragraph\x00 here."
    assert clean_text(raw) == "A comprehension is a concise way. Still same paragraph.\n\nNew paragraph here."


def test_chunks_never_cross_pages_and_respect_size():
    long_page = " ".join(f"Sentence number {i} explains an idea about topic {i % 7}." for i in range(120))
    chunks = chunk_pages([Page(1, "Short page one."), Page(2, long_page), Page(3, "Last page.")], max_chars=400, overlap=60)
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert all(len(c.text) <= 400 for c in chunks)
    assert {c.page_number for c in chunks} == {1, 2, 3}
    page2 = [c for c in chunks if c.page_number == 2]
    assert len(page2) > 3 and page2[0].text.startswith("Sentence number 0")
    joined = " ".join(c.text for c in page2)
    assert "Sentence number 119" in joined                           # nothing dropped


def test_chunker_handles_unbroken_text_and_empty_input():
    assert chunk_page("x" * 2500, max_chars=1000, overlap=100)
    assert all(len(c) <= 1000 for c in chunk_page("x" * 2500, max_chars=1000, overlap=100))
    assert chunk_pages([]) == []
