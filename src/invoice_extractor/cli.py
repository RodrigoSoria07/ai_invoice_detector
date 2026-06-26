"""Command-line interface (R5): ``extract-invoice <file> [--json]``."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from .errors import InvoiceExtractorError
from .extractor import extract_invoice
from .models import Invoice
from .text_extraction import TextExtractor


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract-invoice",
        description="Extract structured data from an invoice PDF/image — fully offline.",
    )
    parser.add_argument("file", help="Path to the invoice file (.pdf, .png, .jpg).")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON instead of a human-readable table.",
    )
    return parser


def _render_table(invoice: Invoice) -> str:
    lines = [
        f"Vendor        : {invoice.vendor}",
        f"Invoice #     : {invoice.invoice_number}",
        f"Date          : {invoice.date.isoformat()}",
        f"Currency      : {invoice.currency}",
        f"Total         : {invoice.total}",
        "Line items:",
    ]
    for item in invoice.line_items:
        lines.append(
            f"  - {item.description}: {item.quantity} x {item.unit_price} = {item.amount}"
        )
    return "\n".join(lines)


def _render_json(invoice: Invoice) -> str:
    return json.dumps(invoice.model_dump(mode="json"), indent=2)


def main(argv: Sequence[str] | None = None, extractor: TextExtractor | None = None) -> int:
    """Entry point. ``extractor`` is injectable so tests avoid real files/Tesseract."""
    args = _build_parser().parse_args(argv)

    try:
        invoice = extract_invoice(args.file, extractor)
    except (FileNotFoundError, InvoiceExtractorError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    output = _render_json(invoice) if args.json else _render_table(invoice)
    print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
