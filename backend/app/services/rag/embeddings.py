"""Embedding service. Vectors come from the project's existing provider layer (Ollama, default bge-m3), which is
multilingual, so a Telugu question can match an English PDF. Groq has no embeddings endpoint, so this stays
local and free even when chat uses Groq."""
import numpy as np

from app.config import settings
from app.services.ai.base import AIError
from app.services.ai.ollama import OllamaProvider

BATCH = 16
_EMPTY = "The embedding model returned no vectors. Check OLLAMA_EMBED_MODEL and try again."


def model_name() -> str:
    return settings.ollama_embed_model


def normalise(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.where(norms == 0, 1.0, norms)


async def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (n, dim) float32 matrix of L2-normalised vectors, so a dot product is cosine similarity."""
    provider = OllamaProvider()
    rows: list[list[float]] = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        got = await provider.embed(batch)
        if len(got) != len(batch):
            raise AIError(_EMPTY, 502)
        rows.extend(got)
    if not rows:
        raise AIError(_EMPTY, 502)
    return normalise(np.asarray(rows, dtype=np.float32))


async def status() -> dict:
    """Is the embedding model ready? Shown in the Documents UI so setup problems are visible before an upload."""
    info = await OllamaProvider().health()
    ready = bool(info["reachable"] and info["embed_model_available"])
    return {"ready": ready, "model": info["embed_model"], "hint": None if ready else info["hint"]}
