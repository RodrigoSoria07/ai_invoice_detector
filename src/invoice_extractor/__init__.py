"""ai-invoice-extractor: offline, rule-based invoice extraction with a mockable text boundary."""

from __future__ import annotations

from .errors import (
    InvoiceExtractorError,
    InvoiceValidationError,
    ParsingError,
    TextExtractionError,
    UnsupportedFormatError,
)
from .extractor import extract_invoice
from .models import Invoice, LineItem
from .parser import parse_invoice
from .text_extraction import LocalTextExtractor, TextExtractor
from .validation import validate_totals

__all__ = [
    "Invoice",
    "InvoiceExtractorError",
    "InvoiceValidationError",
    "LineItem",
    "LocalTextExtractor",
    "ParsingError",
    "TextExtractionError",
    "TextExtractor",
    "UnsupportedFormatError",
    "extract_invoice",
    "parse_invoice",
    "validate_totals",
]
