"""Tests for the LLM parsing path (R3, R6). No network, no API key — the model
call is always mocked behind the LLMClient protocol."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from invoice_extractor.errors import LLMResponseError
from invoice_extractor.extractor import extract_invoice
from invoice_extractor.llm import parse_invoice_with_llm
from invoice_extractor.models import Invoice

from .conftest import FakeLLMClient


def test_parse_invoice_with_llm_returns_expected_invoice(llm_response_json: str) -> None:
    client = FakeLLMClient(llm_response_json)

    invoice = parse_invoice_with_llm("any invoice text", client)

    assert isinstance(invoice, Invoice)
    assert invoice.vendor == "Acme Corp"
    assert invoice.total == Decimal("1300.00")
    assert len(invoice.line_items) == 2
    # The text was actually routed through the client (no I/O magic).
    assert client.prompts == ["any invoice text"]


def test_parse_invoice_with_llm_strips_code_fences(llm_response_json: str) -> None:
    fenced = f"```json\n{llm_response_json}\n```"
    invoice = parse_invoice_with_llm("text", FakeLLMClient(fenced))
    assert invoice.vendor == "Acme Corp"


def test_parse_invoice_with_llm_raises_on_non_json() -> None:
    client = FakeLLMClient("Sure! Here is the invoice you asked for.")
    with pytest.raises(LLMResponseError):
        parse_invoice_with_llm("text", client)


def test_parse_invoice_with_llm_raises_on_schema_mismatch() -> None:
    # Valid JSON, but missing required Invoice fields.
    client = FakeLLMClient('{"vendor": "Acme"}')
    with pytest.raises(LLMResponseError):
        parse_invoice_with_llm("text", client)


def test_extract_invoice_uses_injected_llm(
    sample_pdf: Path, fake_extractor, fake_llm: FakeLLMClient
) -> None:
    invoice = extract_invoice(sample_pdf, fake_extractor, fake_llm)

    assert isinstance(invoice, Invoice)
    assert invoice.vendor == "Acme Corp"
    assert invoice.total == Decimal("1300.00")
    # Both boundaries were exercised: text extraction then LLM parsing.
    assert len(fake_extractor.calls) == 1
    assert len(fake_llm.prompts) == 1


def test_extract_invoice_llm_output_is_still_validated(
    sample_pdf: Path, fake_extractor
) -> None:
    # LLM returns a total that doesn't match its line items → R4 still applies.
    bad = FakeLLMClient(
        '{"vendor": "X", "invoice_number": "1", "date": "2026-01-01", '
        '"currency": "USD", "total": "999.00", '
        '"line_items": [{"description": "a", "quantity": "1", '
        '"unit_price": "10.00", "amount": "10.00"}]}'
    )
    from invoice_extractor.errors import InvoiceValidationError

    with pytest.raises(InvoiceValidationError):
        extract_invoice(sample_pdf, fake_extractor, bad)
