"""Domain-specific exceptions for the invoice extractor."""

from __future__ import annotations


class InvoiceExtractorError(Exception):
    """Base class for all errors raised by this package."""


class UnsupportedFormatError(InvoiceExtractorError):
    """Raised when the input file extension is not a supported invoice format."""


class TextExtractionError(InvoiceExtractorError):
    """Raised when raw text cannot be pulled from the file (bad PDF, OCR failure)."""


class ParsingError(InvoiceExtractorError):
    """Raised when the extracted text cannot be parsed into a valid Invoice."""


class LLMResponseError(ParsingError):
    """Raised when the LLM's response cannot be turned into a valid Invoice.

    A subclass of :class:`ParsingError` so callers that already handle parse
    failures (e.g. the CLI) catch LLM failures too, while tests can assert on
    the LLM path specifically.
    """


class InvoiceValidationError(InvoiceExtractorError):
    """Raised when an invoice fails a business-rule check (e.g. totals mismatch)."""
