"""FastAPI backend for the invoice-extractor web UI.

Thin wrapper around the existing offline pipeline: it accepts an uploaded
invoice, runs ``extract_invoice`` (unchanged), and returns the structured result
as JSON — or a typed error. It also serves the single-page React frontend.

Run:  python web/server.py   →   http://127.0.0.1:8000
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Make the package importable without an install step.
SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, File, UploadFile  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from invoice_extractor import extract_invoice  # noqa: E402
from invoice_extractor.errors import (  # noqa: E402
    InvoiceValidationError,
    ParsingError,
    TextExtractionError,
    UnsupportedFormatError,
)
from invoice_extractor.extractor import _media_type_for  # noqa: E402
from invoice_extractor.text_extraction import LocalTextExtractor  # noqa: E402


def _safe_extract_text(path: str) -> str:
    """Best-effort raw text for debugging; never raises."""
    try:
        media_type = _media_type_for(Path(path))
        return LocalTextExtractor().extract_text(
            file_bytes=Path(path).read_bytes(), media_type=media_type
        )
    except Exception:
        return ""

app = FastAPI(title="Invoice Extractor", docs_url="/api/docs")

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Map each known error to a stable code + a friendly hint the UI can show.
_ERROR_MAP: dict[type[Exception], tuple[str, str]] = {
    UnsupportedFormatError: ("unsupported_format", "This file type isn't supported."),
    FileNotFoundError: ("not_found", "The file could not be read."),
    TextExtractionError: ("no_text", "No readable text was found in the document."),
    ParsingError: ("unparseable", "Couldn't locate invoice fields in the document."),
    InvoiceValidationError: ("totals_mismatch", "The line items don't add up to the total."),
}


@app.post("/api/extract")
async def api_extract(file: UploadFile = File(...)) -> JSONResponse:  # noqa: B008
    """Extract structured data from one uploaded invoice."""
    suffix = Path(file.filename or "").suffix
    payload = await file.read()

    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(payload)
        tmp.close()
        invoice = extract_invoice(tmp.name)
    except tuple(_ERROR_MAP) as exc:
        code, hint = _ERROR_MAP[type(exc)]
        content = {"ok": False, "error_type": code, "hint": hint, "message": str(exc)}
        # For parsing failures, attach the extracted text so the layout can be
        # inspected (and the parser tuned) without re-uploading the file.
        if code in {"unparseable", "totals_mismatch"}:
            content["extracted_text"] = _safe_extract_text(tmp.name)[:4000]
        return JSONResponse(status_code=422, content=content)
    except Exception as exc:  # unexpected — surface a generic message
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error_type": "internal",
                "hint": "Something went wrong while processing the file.",
                "message": str(exc),
            },
        )
    finally:
        os.unlink(tmp.name)

    return JSONResponse(
        content={"ok": True, "filename": file.filename, "invoice": invoice.model_dump(mode="json")}
    )


# Serve the SPA. Mounted last so /api/* routes take precedence.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    print("Invoice Extractor UI -> http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
