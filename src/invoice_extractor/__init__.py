"""ai-invoice-extractor: invoice extraction with mockable text and LLM boundaries.

Offline rule-based parsing by default; optional LLM-driven parsing via a
mockable :class:`LLMClient`.
"""

from __future__ import annotations

from .errors import (
    InvoiceExtractorError,
    InvoiceValidationError,
    LLMResponseError,
    ParsingError,
    TextExtractionError,
    UnsupportedFormatError,
)
from .extractor import extract_invoice
from .llm import AnthropicClient, LLMClient, parse_invoice_with_llm
from .models import Invoice, LineItem
from .parser import parse_invoice
from .text_extraction import LocalTextExtractor, TextExtractor
from .validation import validate_totals

__all__ = [
    "AnthropicClient",
    "Invoice",
    "InvoiceExtractorError",
    "InvoiceValidationError",
    "LLMClient",
    "LLMResponseError",
    "LineItem",
    "LocalTextExtractor",
    "ParsingError",
    "TextExtractionError",
    "TextExtractor",
    "UnsupportedFormatError",
    "extract_invoice",
    "parse_invoice",
    "parse_invoice_with_llm",
    "validate_totals",
]
