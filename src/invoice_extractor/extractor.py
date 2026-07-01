"""Top-level extraction pipeline (R1, R6).

``extract_invoice`` is the single importable entry point: given a file path it
returns a validated :class:`Invoice` or raises a controlled, typed error. By
default it runs fully offline — extract text locally, parse it with rules,
validate. Pass an :class:`LLMClient` to parse the text with an LLM instead.
"""

from __future__ import annotations

from pathlib import Path

from .errors import UnsupportedFormatError
from .llm import LLMClient, parse_invoice_with_llm
from .models import Invoice
from .parser import parse_invoice
from .text_extraction import LocalTextExtractor, TextExtractor
from .validation import validate_totals

# Supported extensions mapped to the media type handed to the text extractor.
SUPPORTED_FORMATS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def _media_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        return SUPPORTED_FORMATS[suffix]
    except KeyError:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise UnsupportedFormatError(
            f"Unsupported file format '{suffix or path.name}'. Supported: {supported}."
        ) from None


def extract_invoice(
    path: str | Path,
    extractor: TextExtractor | None = None,
    llm: LLMClient | None = None,
) -> Invoice:
    """Extract a validated :class:`Invoice` from ``path``.

    ``extractor`` is the (injectable) text-extraction backend; it defaults to the
    offline :class:`LocalTextExtractor`. Tests pass a fake to avoid touching real
    files or Tesseract.

    ``llm`` selects how the extracted text is turned into an :class:`Invoice`:
    when ``None`` (the default) the offline rule-based parser is used; when an
    :class:`LLMClient` is given, the text is parsed by the LLM instead. Either
    way the result is validated the same.

    Raises:
        FileNotFoundError: the path does not exist (R6).
        UnsupportedFormatError: the extension is not a supported format (R6).
        TextExtractionError: the document yielded no readable text (R6).
        ParsingError: the text could not be parsed into an Invoice; the LLM path
            raises the ``LLMResponseError`` subclass on unparseable output (R6).
        InvoiceValidationError: line items do not sum to the total (R4).
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No such invoice file: {path}")

    media_type = _media_type_for(path)
    if extractor is None:
        extractor = LocalTextExtractor()

    text = extractor.extract_text(file_bytes=path.read_bytes(), media_type=media_type)
    invoice = parse_invoice_with_llm(text, llm) if llm is not None else parse_invoice(text)
    return validate_totals(invoice)
