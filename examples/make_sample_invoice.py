"""Generate a sample invoice PDF for demos and manual testing.

Run:  python examples/make_sample_invoice.py
Produces: examples/sample_invoice.pdf

Uses a monospaced font and space-padded columns so the PDF text layer extracts
back cleanly with pdfplumber (the same layout the rule-based parser expects).
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

LINES = [
    "Acme Corp",
    "123 Market Street, Springfield",
    "support@acme.example",
    "",
    "INVOICE",
    "",
    "Invoice #: INV-2026-001",
    "Invoice Date: 2026-06-01",
    "Currency: USD",
    "",
    "Description                 Qty    Unit Price      Amount",
    "Consulting services          10        100.00     1000.00",
    "Managed hosting               1        300.00      300.00",
    "",
    "Subtotal:                                         1300.00",
    "Tax (0%):                                            0.00",
    "Total:                            USD             1300.00",
]


def main() -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", size=11)
    for line in LINES:
        pdf.cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    out = Path(__file__).parent / "sample_invoice.pdf"
    pdf.output(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
