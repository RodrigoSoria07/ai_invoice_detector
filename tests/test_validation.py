"""Tests for total-coherence validation (R4)."""

from __future__ import annotations

import pytest

from invoice_extractor.errors import InvoiceValidationError
from invoice_extractor.models import Invoice
from invoice_extractor.validation import validate_totals


def _invoice(total: str, amounts: list[str]) -> Invoice:
    return Invoice.model_validate(
        {
            "vendor": "Acme Corp",
            "invoice_number": "INV-1",
            "date": "2026-06-01",
            "currency": "USD",
            "total": total,
            "line_items": [
                {"description": f"item {i}", "amount": a} for i, a in enumerate(amounts)
            ],
        }
    )


def test_validate_totals_passes_when_sum_matches() -> None:
    invoice = _invoice("1300.00", ["1000.00", "300.00"])
    # Returns the invoice unchanged and does not raise.
    assert validate_totals(invoice) is invoice


def test_validate_totals_fails_on_mismatch() -> None:
    invoice = _invoice("1300.00", ["1000.00", "250.00"])
    with pytest.raises(InvoiceValidationError):
        validate_totals(invoice)


def test_validate_totals_skips_when_no_line_items() -> None:
    # Nothing to reconcile -> accept the total as-is (no exception).
    invoice = _invoice("88.91", [])
    assert validate_totals(invoice) is invoice
