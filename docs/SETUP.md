# Orin — Setup

## Quick start with Groq (recommended)
1. Go to https://console.groq.com -> **API Keys** -> **Create API Key**. Copy it right away (it is shown once).
2. Open `backend/.env` and paste it: `GROQ_API_KEY=gsk_...`  (never share this key or commit `.env`).
3. Start the backend and frontend (steps 5 and 6 below). No Ollama needed for chat.

Switch providers any time with `AI_PROVIDER=groq | xai | ollama` in `backend/.env` and restart the backend.
xAI Grok: create a key at https://console.x.ai, set `AI_PROVIDER=xai` and `XAI_API_KEY`.

Ollama (steps 1-4) is now optional: only needed for `AI_PROVIDER=ollama` and, later, for free local RAG embeddings.

---

## 1. Install Ollama
Download from https://ollama.com/download (macOS / Windows / Linux) and verify: `ollama --version`.

## 2. Pull a chat model
Pick one and put the same name in `backend/.env` as `OLLAMA_MODEL`.
Local models differ a lot in Telugu/Tamil/etc. quality — **test your demo prompt** before choosing.
```bash
ollama pull qwen2.5:7b      # good default; try llama3.1:8b, gemma2:9b, aya-expanse:8b too
```

## 3. Pull an embedding model (used from Phase 5, RAG)
```bash
ollama pull bge-m3          # multilingual: works for Telugu question + English PDF
```

## 4. Start Ollama
```bash
ollama serve                # skip if the desktop app is already running
```

## 5. Start the backend
```bash
cd backend
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # then edit JWT_SECRET and model names
uvicorn app.main:app --reload --port 8000
```
Check http://localhost:8000/api/health — it tells you if Ollama is down or a model is missing.
Run tests: `python -m pytest`

## 6. Start the frontend
```bash
cd frontend
npm install
npm run dev                                         # http://localhost:5173
```

## Image questions (vision)
Orin can explain an image a student attaches (diagram, maths problem, handwritten note, code/error screenshot, chart).

- **Text vs vision models:** normal chat keeps using `GROQ_MODEL` / `XAI_MODEL` / `OLLAMA_MODEL`. Those default models cannot read images, so any message with an image is sent to a separate vision model. Orin never sends an image to a text-only model, and never pretends to analyse one.
- **Groq (default):** works with your existing `GROQ_API_KEY`. `GROQ_VISION_MODEL=qwen/qwen3.8-27b` is the default. Groq changes its vision lineup often, so if `/api/health` shows `vision.available: false`, pick a current vision model from https://console.groq.com/docs/vision and set it in `backend/.env`.
- **xAI:** set `XAI_VISION_MODEL` to a Grok model that accepts images (not assumed).
- **Ollama:** set `OLLAMA_VISION_MODEL` to a vision model, e.g. `ollama pull qwen2.5vl:7b` (or `llava`), then set the same name in `.env`.
- **Different provider for vision only:** set `VISION_PROVIDER=groq|xai|ollama` (blank = same as `AI_PROVIDER`).
- **Limits:** `MAX_IMAGE_MB` (default 4) is enforced by the server and read by the UI. JPG, PNG and WEBP only; the real file type is checked, not just the file name.
- **Storage:** images are saved under `UPLOAD_DIR` (default `backend/uploads/`, git-ignored) and deleted with their conversation. They are only served to the student who owns them.
- **Check it:** http://localhost:8000/api/health has a `vision` block (`configured`, `available`, `hint`).

## Documents + RAG
Upload study materials on the **Documents** page, then click **Ask Questions** (one document) or **Ask across all documents**.

- **Embeddings need Ollama** even when chat uses Groq (Groq has no embeddings endpoint): `ollama pull bge-m3` and keep `ollama serve` running. The Documents page shows a banner if the embedding model is not ready. `bge-m3` is multilingual, so a Telugu question can match an English PDF.
- **Chat** uses your normal `AI_PROVIDER` model. Answers are built only from retrieved passages and cite `document, page`. Page numbers come from the retrieved passages, never invented; `.txt`/`.md` files have no pages, so only the file name is cited.
- **Vector store:** vectors are stored in the existing SQLite database (`document_chunks.embedding`) and searched with cosine similarity (numpy). No extra server. Deleting a document deletes its vectors and its file.
- **Settings** (`backend/.env`, all optional): `MAX_DOC_MB` (default 25), `RAG_TOP_K` (default 6, doubled when asking across several documents), `RAG_MIN_SCORE` (default 0.30). If Orin says "not found" for things that are in your document, lower `RAG_MIN_SCORE` (try 0.2); if it answers from irrelevant passages, raise it. The backend logs the best score for every question (`RAG retrieve: best score ...`) to help you tune it.
- **Files** are stored under `UPLOAD_DIR/documents/<user id>/` with server-generated names (git-ignored). Only the owner can read, ask about or delete a document.
- **Not supported yet:** scanned/image-only PDFs (no OCR), password-protected PDFs, `.docx`/`.pptx`.
- If you change `OLLAMA_EMBED_MODEL`, documents must be re-processed (Retry) because vectors from different models are not comparable; Orin tells you when this is needed.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "Can't reach Ollama" | Run `ollama serve`; check `OLLAMA_BASE_URL` |
| "Model ... is not installed" | `ollama pull <model>` |
| "Image questions need a vision model" | Set the `*_VISION_MODEL` for your provider in `backend/.env` and restart |
| "could not process this image" | Try a smaller/clearer image; check the vision model name supports images |
| Document stays Failed with "Can't reach Ollama" | Run `ollama serve` and `ollama pull bge-m3`, then click Retry on the document |
| "No readable text was found" | The PDF is scanned/image-only; upload a text-based PDF |
| Slow first reply | The model is loading into memory; use a smaller model or raise `OLLAMA_TIMEOUT_SECONDS` |
