"""Tests for the extraction pipeline (R1, R3, R6)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from invoice_extractor.errors import ParsingError, UnsupportedFormatError
from invoice_extractor.extractor import extract_invoice
from invoice_extractor.models import Invoice

from .conftest import FakeTextExtractor


def test_extract_invoice_uses_injected_extractor(
    sample_pdf: Path, fake_extractor: FakeTextExtractor
) -> None:
    invoice = extract_invoice(sample_pdf, fake_extractor)

    assert isinstance(invoice, Invoice)
    assert invoice.vendor == "Acme Corp"
    assert invoice.total == Decimal("1300.00")
    # The pipeline actually called the injected extractor with the file bytes (no I/O magic).
    assert len(fake_extractor.calls) == 1
    assert fake_extractor.calls[0]["media_type"] == "application/pdf"


def test_extract_invoice_raises_on_unsupported_format(
    tmp_path: Path, fake_extractor: FakeTextExtractor
) -> None:
    txt = tmp_path / "invoice.txt"
    txt.write_text("just text", encoding="utf-8")
    with pytest.raises(UnsupportedFormatError):
        extract_invoice(txt, fake_extractor)


def test_extract_invoice_raises_on_missing_file(fake_extractor: FakeTextExtractor) -> None:
    with pytest.raises(FileNotFoundError):
        extract_invoice("does/not/exist.pdf", fake_extractor)


def test_extract_invoice_raises_on_unparseable_text(sample_pdf: Path) -> None:
    garbage = FakeTextExtractor("This document has no invoice fields whatsoever.")
    with pytest.raises(ParsingError):
        extract_invoice(sample_pdf, garbage)
