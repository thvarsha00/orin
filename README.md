# Orin — Learn. Code. Evolve.
Multilingual AI learning + coding platform for Indian students, powered by **Groq / xAI Grok / local Ollama** (switch with `AI_PROVIDER`).
Stack: FastAPI + SQLAlchemy (SQLite) · React + Vite + TypeScript + Tailwind v4. See `docs/SETUP.md`.

## Status (honest)
| Phase | Feature | State |
|---|---|---|
| 1 | Architecture, config, health check | Done |
| 2 | JWT auth, profiles, full 14-table schema | Done (auth tested) |
| 3 | Ollama provider (chat/stream/json/embed/health) | Done, tested against a mock server; **run against your real model** |
| 4 | Multilingual AI Tutor (streaming, history, level + language) | Done (basic); image questions (vision) added; voice input and learning-context panel TODO |
| 4b | Multilingual engine: LanguageDetector → LanguageProfile → PromptBuilder (8 languages, Roman/native script, slang mirroring) | Done, unit-tested; prompt quality depends on your local model |
| 5 | Documents + RAG: upload PDF/notes, page-aware chunking, embeddings, grounded answers with page citations, single- and multi-document chat | Done; tested with a mock embedding/LLM server (see `docs/SETUP.md`), **run against your real Ollama + Groq** |
| 6 | Orin Code assistant | TODO |
| 7 | Sandboxed code execution (Docker) | TODO, must be Docker-isolated, never in-process |
| 8 | Practice platform + Monaco | TODO |
| 9-10 | Progress + adaptive recommendations | TODO (tables exist) |
| 11-12 | UI polish, testing, deployment | TODO |

Stub pages are labelled "TODO — not implemented yet" in the UI.

## Multilingual engine
`backend/app/services/language/`: `config.py` (add a language here), `detector.py`, `profile.py`, `prompt_builder.py`. The tutor persona lives in `prompts/tutor_core.md` (edit it freely); each request appends a short profile block (Language / Script / Tone / Technical vocabulary / Level). Every module must build prompts via `build_system_prompt(task, profile, level)`; tasks for RAG, debug, hints, quiz, recommendations etc. are already defined.

## Image questions (vision)
Students can attach a JPG/PNG/WEBP (button, drag-and-drop or paste) and ask Orin to explain it in their chosen language and script. Text-only chat still uses your normal text model; messages with an image go to a separate **vision model** (`GROQ_VISION_MODEL`, default `qwen/qwen3.8-27b`) because the default text models (`gpt-oss-120b`, `qwen2.5:7b`) cannot read images. See "Image questions" in `docs/SETUP.md`.

## Documents + RAG
Students upload a PDF (or `.txt` / `.md` notes) on the **Documents** page and ask questions grounded in it, for one document or across all of them.

```
Upload -> extract text per page -> clean -> page-aware chunks -> embeddings (Ollama bge-m3)
       -> stored in SQLite (document_chunks.embedding) -> cosine search -> top passages
       -> LLM (your AI_PROVIDER) with the passages as context -> answer + sources (document, page, snippet)
```
Code: `backend/app/services/rag/` (`extraction`, `chunking`, `embeddings`, `vector_store`, `ingestion`, `retrieval`, `answer`), `backend/app/api/documents.py`, `frontend/src/pages/Documents.tsx` and `DocumentChat.tsx`. If no passage is similar enough to the question, Orin says it was not found in the uploaded materials and does not call the LLM. See "Documents + RAG" in `docs/SETUP.md`.
