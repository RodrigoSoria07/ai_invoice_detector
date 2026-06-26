"""Shared test fixtures and fakes — fully offline, no Tesseract, no real PDFs."""

from __future__ import annotations

from pathlib import Path

import pytest

from invoice_extractor.text_extraction import TextExtractor

FIXTURES = Path(__file__).parent / "fixtures"


class FakeTextExtractor:
    """A :class:`TextExtractor` that returns fixed, canned text.

    Records each call so tests can assert the pipeline passed the file through.
    """

    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[dict[str, object]] = []

    def extract_text(self, *, file_bytes: bytes, media_type: str) -> str:
        self.calls.append({"file_bytes": file_bytes, "media_type": media_type})
        return self.text


@pytest.fixture
def sample_text() -> str:
    return (FIXTURES / "sample_invoice_text.txt").read_text(encoding="utf-8")


@pytest.fixture
def fake_extractor(sample_text: str) -> FakeTextExtractor:
    extractor = FakeTextExtractor(sample_text)
    assert isinstance(extractor, TextExtractor)  # honors the Protocol (R3)
    return extractor


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """A throwaway file with a supported extension (contents irrelevant — extractor is faked)."""
    path = tmp_path / "invoice.pdf"
    path.write_bytes(b"%PDF-1.4 fake bytes")
    return path
