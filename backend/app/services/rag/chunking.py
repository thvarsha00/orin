"""Page-aware chunking: a chunk never spans two pages, so every retrieved passage has one true page number."""
import re
from dataclasses import dataclass

from app.services.rag.extraction import Page

MAX_CHARS = 1000
OVERLAP_CHARS = 150
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    index: int
    page_number: int | None
    text: str


def _pieces(paragraph: str, limit: int) -> list[str]:
    """Split an over-long paragraph on sentences, then on words, so nothing exceeds `limit`."""
    if len(paragraph) <= limit:
        return [paragraph]
    out, cur = [], ""
    for sentence in _SENTENCE.split(paragraph):
        while len(sentence) > limit:  # no sentence boundary: cut on a space
            cut = sentence.rfind(" ", 0, limit)
            cut = cut if cut > limit // 2 else limit
            if cur:
                out.append(cur)
                cur = ""
            out.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if cur and len(cur) + 1 + len(sentence) > limit:
            out.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        out.append(cur)
    return [p for p in out if p]


def _tail(text: str, size: int) -> str:
    """Last ~`size` chars starting at a word boundary (context carried into the next chunk)."""
    if len(text) <= size:
        return text
    tail = text[-size:]
    space = tail.find(" ")
    return tail[space + 1:] if 0 <= space < size // 2 else tail


def chunk_page(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    units = [u for p in text.split("\n\n") for u in _pieces(p, max_chars)]
    chunks, cur = [], ""
    for unit in units:
        if cur and len(cur) + 2 + len(unit) > max_chars:
            chunks.append(cur)
            carry = _tail(cur, overlap)
            cur = f"{carry}\n\n{unit}" if len(carry) + 2 + len(unit) <= max_chars else unit
        else:
            cur = f"{cur}\n\n{unit}" if cur else unit
    if cur:
        chunks.append(cur)
    return chunks


def chunk_pages(pages: list[Page], max_chars: int = MAX_CHARS, overlap: int = OVERLAP_CHARS) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page in pages:
        for text in chunk_page(page.text, max_chars, overlap):
            chunks.append(Chunk(len(chunks), page.number, text))
    return chunks
