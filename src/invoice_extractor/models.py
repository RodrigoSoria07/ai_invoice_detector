"""Pydantic models describing a structured invoice (R2)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class LineItem(BaseModel):
    """A single line on an invoice.

    ``amount`` is the extended price for the line (typically ``quantity *
    unit_price``) and is what gets summed when validating against the invoice
    total.
    """

    model_config = ConfigDict(extra="forbid")

    description: str
    quantity: Decimal = Field(default=Decimal("1"))
    unit_price: Decimal = Field(default=Decimal("0"))
    amount: Decimal


class Invoice(BaseModel):
    """Structured representation of an invoice (R2)."""

    model_config = ConfigDict(extra="forbid")

    vendor: str
    invoice_number: str
    date: date
    currency: str
    total: Decimal
    line_items: list[LineItem] = Field(default_factory=list)
