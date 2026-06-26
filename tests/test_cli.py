"""Tests for the CLI (R5)."""

from __future__ import annotations

import json
from pathlib import Path

from invoice_extractor.cli import main

from .conftest import FakeTextExtractor


def test_cli_outputs_json_flag(
    sample_pdf: Path, fake_extractor: FakeTextExtractor, capsys
) -> None:
    exit_code = main([str(sample_pdf), "--json"], extractor=fake_extractor)

    assert exit_code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)  # must be valid JSON
    assert payload["vendor"] == "Acme Corp"
    assert payload["total"] == "1300.00"
    assert len(payload["line_items"]) == 2


def test_cli_table_output(sample_pdf: Path, fake_extractor: FakeTextExtractor, capsys) -> None:
    exit_code = main([str(sample_pdf)], extractor=fake_extractor)

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Acme Corp" in out
    assert "INV-2026-001" in out


def test_cli_reports_error_for_missing_file(
    fake_extractor: FakeTextExtractor, capsys
) -> None:
    exit_code = main(["nope.pdf"], extractor=fake_extractor)

    assert exit_code == 1
    assert "error:" in capsys.readouterr().err
