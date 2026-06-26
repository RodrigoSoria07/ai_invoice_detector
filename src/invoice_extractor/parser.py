"""Rule-based parser: extracted text -> structured :class:`Invoice`.

Pure, deterministic, offline. No AI, no network. This is where the real logic
lives, so it is the most heavily tested module. The heuristics aim to cover
common real-world layouts (classic tables and Stripe/Anthropic-style invoices
with multi-line descriptions).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .errors import ParsingError
from .models import Invoice, LineItem

# --- currency -------------------------------------------------------------

SYMBOL_TO_CODE = {"$": "USD", "€": "EUR", "£": "GBP"}
KNOWN_CODES = {"USD", "EUR", "GBP", "CAD", "AUD", "MXN", "ARS", "BRL", "JPY"}

# --- invoice number -------------------------------------------------------

# Explicit label, e.g. "Invoice #: INV-001", "Invoice No 5567", "Invoice number L68T9EET-0004".
_INVOICE_NO = re.compile(
    r"invoice\s*(?:#|no\.?|number)\s*[:#]?\s*([A-Za-z0-9][A-Za-z0-9\-/]*)",
    re.IGNORECASE,
)
# Fallback: a standalone token like "INV-2026-001" (must contain a digit so it
# never matches the word "Invoice" itself).
_INVOICE_NO_FALLBACK = re.compile(r"\b(INV[-/]?\d[A-Za-z0-9\-/]*)\b", re.IGNORECASE)

# --- vendor ---------------------------------------------------------------

_VENDOR_LABEL = re.compile(
    r"^\s*(?:vendor|from|seller|bill\s*from|sold\s*by)\s*[:\-]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Lines that are clearly metadata/labels, not the vendor name.
_VENDOR_SKIP = re.compile(
    r"^(?:invoice\b|nvoice\b|invoice\s*(?:#|no|number)|date\b|bill\s+to|bill\s+from|"
    r"ship\s+to|sold\s+by|payment\b|description\b|subtotal\b|total\b|amount\b|tax\b)",
    re.IGNORECASE,
)
_AMOUNT_ONLY = re.compile(r"^[$€£]?\s*[\d,]+(?:\.\d{2})?$")

# --- totals ---------------------------------------------------------------

# "Total", "Amount Due", "Balance Due", "Grand Total" — but NOT "Subtotal".
_TOTAL = re.compile(
    r"(?<![A-Za-z])(?:grand\s*total|amount\s*due|balance\s*due|total\s*due|total)\s*"
    r"[:\-]?\s*(?:[$€£]|[A-Z]{3})?\s*([\d][\d,]*\.\d{2})",
    re.IGNORECASE,
)

# --- line items -----------------------------------------------------------

# Classic table row: "<description>  <qty>  <unit price>  <amount>" on one line.
_LINE_ITEM = re.compile(
    r"^\s*(?P<desc>.+?)\s+"
    r"(?P<qty>\d+(?:\.\d+)?)\s+"
    r"(?:[$€£]\s*)?(?P<unit>\d[\d,]*\.\d{2})\s+"
    r"(?:[$€£]\s*)?(?P<amount>\d[\d,]*\.\d{2})\s*$",
)
# Start/stop markers for the section-based parser (multi-line descriptions).
_SECTION_HEADER = re.compile(r"description\b.*\b(?:amount|total|price)\b", re.IGNORECASE)
_SECTION_STOP = re.compile(
    r"^\s*(?:sub\s*total|total|amount\s+due|tax\b|balance\b|discount\b)", re.IGNORECASE
)
# A row that is just an optional qty followed by a money amount, e.g. "1 $88.91".
_AMOUNT_ROW = re.compile(
    r"^\s*(?:(?P<qty>\d+(?:\.\d+)?)\s+)?(?:[$€£]\s*)?(?P<amount>\d[\d,]*\.\d{2})\s*$"
)

# --- dates ----------------------------------------------------------------

_MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)
# Each pattern captures a date *value*; the formats are tried in order.
_DATE_VALUE_PATTERNS: tuple[tuple[re.Pattern[str], tuple[str, ...]], ...] = (
    (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), ("%Y-%m-%d",)),
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"), ("%d/%m/%Y", "%m/%d/%Y")),
    (re.compile(r"\b(\d{1,2}-\d{1,2}-\d{4})\b"), ("%d-%m-%Y", "%m-%d-%Y")),
    (
        re.compile(rf"\b((?:{_MONTHS})\.?\s+\d{{1,2}},?\s+\d{{4}})\b", re.IGNORECASE),
        ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"),
    ),
    (
        re.compile(rf"\b(\d{{1,2}}\s+(?:{_MONTHS})\.?\s+\d{{4}})\b", re.IGNORECASE),
        ("%d %B %Y", "%d %b %Y"),
    ),
)


def _money(raw: str) -> Decimal:
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation as exc:  # pragma: no cover - regex already constrains this
        raise ParsingError(f"Could not parse money value {raw!r}.") from exc


def _extract_date(text: str) -> date | None:
    """Return the first parseable date *value* found in ``text``, or None."""
    for pattern, formats in _DATE_VALUE_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        raw = m.group(1).strip().rstrip(".")
        # Normalize a 4-letter abbreviation like "Sept" that strptime rejects.
        raw = re.sub(r"\bSept\b", "Sep", raw)
        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue
    return None


def _find_date(text: str) -> date:
    """Find the invoice date, preferring an issue-date line over any date."""
    lines = text.splitlines()
    issue = [
        ln for ln in lines
        if re.search(r"invoice\s*date|date\s*of\s*issue|date\s*issued|issued", ln, re.IGNORECASE)
    ]
    any_date = [ln for ln in lines if re.search(r"\bdate\b", ln, re.IGNORECASE)]
    for group in (issue, any_date, [text]):
        for chunk in group:
            found = _extract_date(chunk)
            if found is not None:
                return found
    raise ParsingError("Could not find a parseable date in the document text.")


def _find_vendor(text: str, lines: list[str]) -> str:
    match = _VENDOR_LABEL.search(text)
    if match:
        return match.group(1).strip()
    # Otherwise: the first line that isn't a label, metadata, or a bare amount.
    for line in lines:
        stripped = line.strip()
        if not stripped or _VENDOR_SKIP.match(stripped) or _AMOUNT_ONLY.match(stripped):
            continue
        return stripped
    # Last resort: the first non-empty line.
    for line in lines:
        if line.strip():
            return line.strip()
    raise ParsingError("Could not determine the vendor.")


def _find_currency(text: str) -> str:
    for code in KNOWN_CODES:
        if re.search(rf"(?<![A-Za-z]){code}(?![A-Za-z])", text):
            return code
    for symbol, code in SYMBOL_TO_CODE.items():
        if symbol in text:
            return code
    return "USD"  # sensible default; total is still validated downstream


def _classic_line_items(lines: list[str]) -> list[LineItem]:
    items: list[LineItem] = []
    for line in lines:
        m = _LINE_ITEM.match(line)
        if not m:
            continue
        desc = m.group("desc").strip()
        if desc.lower() in {"description", "item", "items"}:
            continue
        items.append(
            LineItem(
                description=desc,
                quantity=_money(m.group("qty")),
                unit_price=_money(m.group("unit")),
                amount=_money(m.group("amount")),
            )
        )
    return items


def _section_line_items(lines: list[str]) -> list[LineItem]:
    """Parse items under a 'Description ... Amount' header where a single item
    may span several lines and the amount row is just '<qty> <amount>'."""
    start = None
    for i, line in enumerate(lines):
        if _SECTION_HEADER.search(line):
            start = i + 1
            break
    if start is None:
        return []

    items: list[LineItem] = []
    desc_parts: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            continue
        if _SECTION_STOP.match(stripped):
            break
        m = _AMOUNT_ROW.match(stripped)
        if m:
            amount = _money(m.group("amount"))
            qty = _money(m.group("qty")) if m.group("qty") else Decimal("1")
            unit = (amount / qty).quantize(Decimal("0.01")) if qty else amount
            items.append(
                LineItem(
                    description=" ".join(desc_parts).strip() or "Item",
                    quantity=qty,
                    unit_price=unit,
                    amount=amount,
                )
            )
            desc_parts = []
        else:
            desc_parts.append(stripped)
    return items


def _find_line_items(lines: list[str]) -> list[LineItem]:
    # Prefer the classic single-line table; fall back to the section parser.
    return _classic_line_items(lines) or _section_line_items(lines)


def parse_invoice(text: str) -> Invoice:
    """Parse plain invoice text into an :class:`Invoice`.

    Raises :class:`ParsingError` when a required field cannot be located.
    """
    lines = text.splitlines()

    inv_match = _INVOICE_NO.search(text) or _INVOICE_NO_FALLBACK.search(text)
    if not inv_match:
        raise ParsingError("Could not find an invoice number in the document text.")

    invoice_date = _find_date(text)

    total_match = _TOTAL.search(text)
    if not total_match:
        raise ParsingError("Could not find a total amount in the document text.")

    return Invoice(
        vendor=_find_vendor(text, lines),
        invoice_number=inv_match.group(1).strip(),
        date=invoice_date,
        currency=_find_currency(text),
        total=_money(total_match.group(1)),
        line_items=_find_line_items(lines),
    )
