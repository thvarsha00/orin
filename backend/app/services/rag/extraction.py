"""Turns an uploaded file into clean, page-aware text. Pure functions: no database, no network."""
import io
import re
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError


class ExtractionError(Exception):
    """`message` is safe to show to students."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class Page:
    number: int | None   # 1-based PDF page; None for plain-text files (no real pages, so none are invented)
    text: str


@dataclass
class Extracted:
    pages: list[Page]
    page_count: int | None


def clean_text(raw: str) -> str:
    """Normalise extractor output: drop control chars, re-join hyphenated line breaks, unwrap hard-wrapped lines
    but keep paragraph breaks (chunking relies on them)."""
    text = raw.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").replace("\u00ad", "")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    paragraphs = [re.sub(r"[ \t\u00a0]+", " ", re.sub(r"\n", " ", p)).strip() for p in re.split(r"\n\s*\n", text)]
    return "\n\n".join(p for p in paragraphs if p)


def extract_pdf(data: bytes) -> Extracted:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ExtractionError("This PDF is password-protected. Remove the password and upload it again.")
        total = len(reader.pages)
        if total == 0:
            raise ExtractionError("This PDF has no pages.")
        pages = []
        for i, page in enumerate(reader.pages, start=1):
            try:
                text = clean_text(page.extract_text() or "")
            except Exception:  # one unreadable page should not sink the whole document
                text = ""
            if text:
                pages.append(Page(i, text))
    except ExtractionError:
        raise
    except (PyPdfError, ValueError, KeyError, OSError, RecursionError):
        raise ExtractionError("This PDF looks corrupted or is not a valid PDF file.")
    if not pages:
        raise ExtractionError("No readable text was found. Scanned or image-only PDFs are not supported yet.")
    return Extracted(pages, total)


def extract_text_file(data: bytes) -> Extracted:
    try:
        raw = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ExtractionError("This text file is not UTF-8 encoded. Save it as UTF-8 and upload it again.")
    text = clean_text(raw)
    if not text:
        raise ExtractionError("This file is empty.")
    return Extracted([Page(None, text)], None)


def extract(data: bytes, file_type: str) -> Extracted:
    return extract_pdf(data) if file_type == "pdf" else extract_text_file(data)
