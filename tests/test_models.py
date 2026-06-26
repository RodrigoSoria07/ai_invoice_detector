"""Tests for the Pydantic invoice models (R2)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from invoice_extractor.models import Invoice


def test_invoice_model_parses_valid_data() -> None:
    invoice = Invoice.model_validate(
        {
            "vendor": "Acme Corp",
            "invoice_number": "INV-2026-001",
            "date": "2026-06-01",
            "currency": "USD",
            "total": "1300.00",
            "line_items": [
                {
                    "description": "Consulting",
                    "quantity": "10",
                    "unit_price": "100.00",
                    "amount": "1000.00",
                },
                {
                    "description": "Hosting",
                    "quantity": "1",
                    "unit_price": "300.00",
                    "amount": "300.00",
                },
            ],
        }
    )

    assert invoice.vendor == "Acme Corp"
    assert invoice.date == date(2026, 6, 1)
    assert invoice.total == Decimal("1300.00")
    assert isinstance(invoice.total, Decimal)
    assert len(invoice.line_items) == 2
    assert invoice.line_items[0].amount == Decimal("1000.00")


def test_invoice_model_rejects_bad_date() -> None:
    with pytest.raises(ValidationError):
        Invoice.model_validate(
            {
                "vendor": "Acme Corp",
                "invoice_number": "INV-2026-001",
                "date": "not-a-date",
                "currency": "USD",
                "total": "0.00",
                "line_items": [],
            }
        )
