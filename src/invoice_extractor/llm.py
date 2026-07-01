"""Optional LLM-driven parsing (R3): extracted text -> structured :class:`Invoice`.

This is the AI path. It mirrors the design of :mod:`text_extraction`: the actual
model call sits behind the :class:`LLMClient` protocol, so tests inject a fake
that returns canned JSON — no network, no API key, no token cost. The parsing
and validation *logic* is what gets tested, not the model.

The offline rule-based parser in :mod:`parser` remains the default; this module
is used only when a client is passed to :func:`extract_invoice`.
"""

from __future__ import annotations

import json
import os
from typing import Protocol, runtime_checkable

from pydantic import ValidationError

from .errors import LLMResponseError
from .models import Invoice

# The model is instructed to return *only* this JSON object — no prose, no fences.
_SYSTEM_PROMPT = """\
You extract structured data from invoice text. Respond with a single JSON object \
and nothing else — no explanation, no markdown code fences.

The object must have exactly these keys:
- "vendor": string, the company that issued the invoice
- "invoice_number": string
- "date": string, the invoice date in ISO format (YYYY-MM-DD)
- "currency": string, the 3-letter ISO currency code (e.g. "USD", "EUR")
- "total": string, the grand total as a plain decimal (e.g. "1300.00")
- "line_items": array of objects, each with:
    - "description": string
    - "quantity": string decimal
    - "unit_price": string decimal
    - "amount": string decimal, the line's extended price

If a field is missing from the text, use your best inference; never invent line \
items that are not present. Amounts must be plain numbers without currency symbols."""


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for anything that turns a prompt into a text completion.

    Kept deliberately minimal and provider-agnostic so tests can inject a fake
    and any LLM backend can be adapted behind it.
    """

    def complete(self, *, prompt: str) -> str:
        """Return the model's text response to ``prompt``."""
        ...


class AnthropicClient:
    """An :class:`LLMClient` backed by Anthropic's Claude models.

    The API key is read from the ``ANTHROPIC_API_KEY`` environment variable and
    never hardcoded (R7). The ``anthropic`` package is imported lazily so the
    rest of the tool — and its test suite — never requires it.
    """

    def __init__(self, model: str = "claude-opus-4-8", max_tokens: int = 4096) -> None:
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, *, prompt: str) -> str:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise LLMResponseError(
                "ANTHROPIC_API_KEY is not set. Export it to use the --llm extractor, "
                "or run without --llm to use the offline parser."
            )
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise LLMResponseError(
                "The 'anthropic' package is required for LLM extraction. "
                "Install it with: pip install 'ai-invoice-extractor[llm]'."
            ) from exc

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        message = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(block.text for block in message.content if block.type == "text")


def _strip_code_fences(raw: str) -> str:
    """Remove a leading ```json / ``` fence if the model wrapped its JSON."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop the opening fence (``` or ```json) and any closing fence.
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_invoice_with_llm(text: str, client: LLMClient) -> Invoice:
    """Parse invoice ``text`` into an :class:`Invoice` using ``client``.

    Raises :class:`LLMResponseError` if the model's output is not valid JSON or
    does not match the :class:`Invoice` schema.
    """
    raw = client.complete(prompt=text)
    payload = _strip_code_fences(raw)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise LLMResponseError(
            f"LLM did not return valid JSON: {exc}. Response was: {raw[:200]!r}"
        ) from exc

    if not isinstance(data, dict):
        raise LLMResponseError(f"LLM returned a JSON {type(data).__name__}, expected an object.")

    try:
        return Invoice.model_validate(data)
    except ValidationError as exc:
        raise LLMResponseError(f"LLM output did not match the Invoice schema: {exc}") from exc
