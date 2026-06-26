"""Text-extraction boundary (R3): turn raw file bytes into plain text.

This is the only part that touches the outside world (the filesystem libs,
Tesseract). It sits behind the :class:`TextExtractor` protocol so tests inject a
fake that returns canned text — no PDFs, no Tesseract install, no flakiness.

There is deliberately **no network call and no API key** anywhere here.
"""

from __future__ import annotations

import io
from typing import Protocol, runtime_checkable

from .errors import TextExtractionError


@runtime_checkable
class TextExtractor(Protocol):
    """Protocol for anything that turns invoice bytes into plain text."""

    def extract_text(self, *, file_bytes: bytes, media_type: str) -> str:
        """Return the document's text content."""
        ...


class LocalTextExtractor:
    """Offline :class:`TextExtractor`.

    * PDFs  -> text layer via ``pdfplumber`` (no OCR needed for digital PDFs).
    * Images -> OCR via ``pytesseract`` (requires the Tesseract binary installed).

    Heavy libraries are imported lazily so importing this package — and running
    its test suite — never requires them.
    """

    def extract_text(self, *, file_bytes: bytes, media_type: str) -> str:
        if media_type == "application/pdf":
            text = self._from_pdf(file_bytes)
        elif media_type.startswith("image/"):
            text = self._from_image(file_bytes)
        else:  # pragma: no cover - guarded earlier by the extractor
            raise TextExtractionError(f"Cannot extract text from media type {media_type!r}.")

        if not text.strip():
            raise TextExtractionError(
                "No text could be extracted from the document "
                "(empty text layer or unreadable scan)."
            )
        return text

    @staticmethod
    def _from_pdf(file_bytes: bytes) -> str:
        try:
            import pdfplumber
        except ImportError as exc:  # pragma: no cover
            raise TextExtractionError("pdfplumber is required to read PDF invoices.") from exc

        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages)

    @staticmethod
    def _from_image(file_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:  # pragma: no cover
            raise TextExtractionError(
                "pytesseract and Pillow are required to read image invoices."
            ) from exc

        with Image.open(io.BytesIO(file_bytes)) as image:
            try:
                return pytesseract.image_to_string(image)
            except pytesseract.TesseractNotFoundError as exc:
                raise TextExtractionError(
                    "Tesseract OCR is not installed (or not on PATH). It is required "
                    "for image invoices (PNG/JPG). PDF invoices work without it. "
                    "See the README for install instructions."
                ) from exc
