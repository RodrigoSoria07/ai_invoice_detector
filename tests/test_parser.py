"""Tests for the rule-based text parser — the offline core."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from invoice_extractor.errors import ParsingError
from invoice_extractor.parser import parse_invoice
from invoice_extractor.validation import validate_totals

FIXTURES = Path(__file__).parent / "fixtures"


def test_parser_extracts_core_fields(sample_text: str) -> None:
    invoice = parse_invoice(sample_text)

    assert invoice.vendor == "Acme Corp"
    assert invoice.invoice_number == "INV-2026-001"
    assert invoice.date == date(2026, 6, 1)
    assert invoice.currency == "USD"
    assert invoice.total == Decimal("1300.00")


def test_parser_extracts_line_items(sample_text: str) -> None:
    invoice = parse_invoice(sample_text)

    assert len(invoice.line_items) == 2
    first = invoice.line_items[0]
    assert first.description == "Consulting services"
    assert first.quantity == Decimal("10")
    assert first.unit_price == Decimal("100.00")
    assert first.amount == Decimal("1000.00")
    # Header, subtotal, tax, and total rows must NOT be picked up as line items.
    assert sum(i.amount for i in invoice.line_items) == Decimal("1300.00")


def test_parser_detects_currency_symbol() -> None:
    text = (
        "Globex Ltd\n"
        "Invoice No: 7788\n"
        "Date: 2026-03-15\n"
        "Total: £450.00\n"
    )
    invoice = parse_invoice(text)
    assert invoice.currency == "GBP"
    assert invoice.total == Decimal("450.00")


def test_parser_ignores_subtotal_and_picks_total() -> None:
    text = (
        "Initech\n"
        "Invoice #: A-100\n"
        "Date: 2026-01-02\n"
        "Subtotal: 90.00\n"
        "Total: 100.00\n"
    )
    invoice = parse_invoice(text)
    assert invoice.total == Decimal("100.00")


def test_parser_raises_when_total_missing() -> None:
    text = "Vendor: Someone\nInvoice #: X-1\nDate: 2026-01-01\n"
    with pytest.raises(ParsingError):
        parse_invoice(text)


def test_parser_raises_on_unparseable_text() -> None:
    with pytest.raises(ParsingError):
        parse_invoice("Just a random note, nothing invoice-like here.")


def test_parser_extracts_date_with_issue_label() -> None:
    text = "Acme\nInvoice number A-1\nDate of issue March 11, 2026\nTotal $10.00\n"
    invoice = parse_invoice(text)
    assert invoice.date == date(2026, 3, 11)


def test_parser_handles_real_world_anthropic_layout() -> None:
    text = (FIXTURES / "anthropic_invoice_text.txt").read_text(encoding="utf-8")
    invoice = parse_invoice(text)

    assert invoice.vendor == "Anthropic, PBC"  # skips "Invoice"/date metadata lines
    assert invoice.invoice_number == "L68T9EET-0004"
    assert invoice.date == date(2026, 3, 11)
    assert invoice.currency == "USD"
    assert invoice.total == Decimal("88.91")
    # Section parser: multi-line description + "1 $88.91" amount row.
    assert len(invoice.line_items) == 1
    assert invoice.line_items[0].amount == Decimal("88.91")
    # Totals reconcile, so the pipeline accepts it.
    assert validate_totals(invoice) is invoice
