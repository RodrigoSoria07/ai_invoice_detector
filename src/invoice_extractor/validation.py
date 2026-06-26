"""Business-rule validation for invoices (R4)."""

from __future__ import annotations

from decimal import Decimal

from .errors import InvoiceValidationError
from .models import Invoice

# Maximum allowed difference between the sum of line items and the invoice total.
TOTAL_TOLERANCE = Decimal("0.01")


def validate_totals(invoice: Invoice, tolerance: Decimal = TOTAL_TOLERANCE) -> Invoice:
    """Ensure the sum of ``line_items`` equals ``total`` within ``tolerance``.

    Returns the invoice unchanged when valid so it can be used in a pipeline.
    Raises :class:`InvoiceValidationError` otherwise.

    When no line items were extracted there is nothing to reconcile, so the
    total is accepted as-is (some real invoices have layouts we can't itemize).
    """
    if not invoice.line_items:
        return invoice
    line_sum = sum((item.amount for item in invoice.line_items), Decimal("0"))
    if abs(line_sum - invoice.total) > tolerance:
        raise InvoiceValidationError(
            f"Line items sum to {line_sum} but invoice total is {invoice.total} "
            f"(tolerance ±{tolerance})."
        )
    return invoice
