# 🧾 invoice-extractor

**Extract structured data from invoice PDFs and images — fully offline, rule-based, with zero API or token cost.**

Point it at a `.pdf`, `.png`, or `.jpg` invoice and get back a validated `Invoice`
object (vendor, invoice number, date, currency, total, line items) as a typed
Python object, a table, or JSON.

```bash
$ extract-invoice examples/sample_invoice.pdf --json
{
  "vendor": "Acme Corp",
  "invoice_number": "INV-2026-001",
  "date": "2026-06-01",
  "currency": "USD",
  "total": "1300.00",
  "line_items": [
    {"description": "Consulting services", "quantity": "10", "unit_price": "100.00", "amount": "1000.00"},
    {"description": "Managed hosting",     "quantity": "1",  "unit_price": "300.00", "amount": "300.00"}
  ]
}
```

> 📽️ **Demo:** _add a GIF here — see [Recording the demo GIF](#recording-the-demo-gif)._
>
> `![demo](docs/demo.gif)`

---

## Why this design

- **No API keys, no network, no per-token cost.** Text is pulled locally
  (`pdfplumber` for PDFs, Tesseract OCR for images) and parsed with deterministic
  rules. The same input always produces the same output.
- **Clean, testable boundary.** The only part that touches the outside world —
  reading file bytes into text — sits behind a small `TextExtractor` protocol.
  Tests inject a fake that returns canned text, so the suite runs in
  milliseconds with **no PDFs, no Tesseract, and no flakiness**. The *logic*
  (parsing, validation, error handling) is what gets tested.
- **Schema-validated output.** Results are [Pydantic](https://docs.pydantic.dev/)
  models, and the line-item amounts must reconcile with the invoice total or you
  get a clear `InvoiceValidationError`.

## Features

| | |
|---|---|
| **R1** | Accept a `.pdf` / `.png` / `.jpg` path → return a validated `Invoice`. |
| **R2** | `Invoice` schema: `vendor`, `invoice_number`, `date`, `currency`, `total` (`Decimal`), `line_items`. |
| **R3** | Text extraction is behind a `TextExtractor` protocol → trivially mockable. |
| **R4** | Coherence check: line items must sum to `total` (±0.01) or raise `InvoiceValidationError`. |
| **R5** | CLI: `extract-invoice <file> [--json]` prints a table or JSON. |
| **R6** | Graceful, typed errors: missing file, unsupported format, unreadable text, unparseable content. |
| **R7** | No secrets anywhere — nothing to leak. |

## Architecture

```
            ┌───────────────────────────────────────────────┐
file path → │  extractor.extract_invoice()                  │
            │    1. validate path + format                  │
            │    2. TextExtractor.extract_text()  ◄── boundary (mocked in tests)
            │    3. parser.parse_invoice(text)    ◄── rule-based core (heavily tested)
            │    4. validation.validate_totals()            │
            └───────────────────────────────────────────────┘ → Invoice (Pydantic)
```

```
src/invoice_extractor/
├─ models.py            # Invoice, LineItem (Pydantic)
├─ text_extraction.py   # TextExtractor protocol + LocalTextExtractor (pdfplumber / Tesseract)
├─ parser.py            # parse_invoice(text) -> Invoice   ← the offline rule engine
├─ extractor.py         # extract_invoice(path, extractor) -> Invoice
├─ validation.py        # validate_totals()
└─ cli.py               # extract-invoice <file> [--json]
```

## Install

```bash
python -m pip install -e ".[dev]"
```

For **image** invoices you also need the Tesseract binary installed
(the Python `pytesseract` wrapper just calls it):

- **Windows:** install [Tesseract at UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and ensure it is on `PATH`.
- **macOS:** `brew install tesseract`
- **Debian/Ubuntu:** `sudo apt install tesseract-ocr`

PDF invoices with a real text layer need **no** Tesseract.

## Usage

### CLI

```bash
extract-invoice path/to/invoice.pdf            # human-readable table
extract-invoice path/to/invoice.pdf --json     # JSON
```

### As a library

```python
from invoice_extractor import extract_invoice

invoice = extract_invoice("invoice.pdf")
print(invoice.vendor, invoice.total)
for item in invoice.line_items:
    print(item.description, item.amount)
```

Need to test your own pipeline without files? Inject any object with an
`extract_text(*, file_bytes, media_type) -> str` method:

```python
class MyExtractor:
    def extract_text(self, *, file_bytes, media_type):
        return "Acme Corp\nInvoice #: INV-1\nDate: 2026-06-01\nTotal: 100.00\n"

extract_invoice("invoice.pdf", MyExtractor())
```

## Web UI

A small drag-and-drop web app drives the same offline pipeline. The Python
extraction is unchanged — a thin FastAPI backend just wraps it and serves a
React frontend. React is served **locally** from `web/static/vendor/` and the
UI is **precompiled** to plain JS (`web/static/app.js`), so the browser does no
CDN fetches and no in-browser compilation — it works fully offline and loads
instantly.

```bash
python -m pip install -e ".[web]"
python web/server.py
# open http://127.0.0.1:8000
```

Drop a `.pdf`/`.png`/`.jpg` invoice and you get summary cards, a line-items
table, a "totals reconciled" badge, and copy/download-JSON actions. Parsing
still runs entirely on your machine — no external API, no token cost. The API
endpoint is `POST /api/extract` (multipart `file`), with interactive docs at
`/api/docs`.

```
web/
├─ server.py                 # FastAPI: POST /api/extract + serves the SPA
├─ src/app.jsx               # UI source (JSX)
├─ build.js                  # node web/build.js → compiles app.jsx to static/app.js
├─ buildtools/babel.min.js   # build-time only (not served)
└─ static/
   ├─ index.html             # page shell + styles
   ├─ app.js                 # compiled UI (committed; regenerate with build.js)
   └─ vendor/                # React, ReactDOM (served locally — no CDN)
```

If you edit `web/src/app.jsx`, regenerate the compiled bundle with
`node web/build.js`.

## How the parser works

`parse_invoice()` uses targeted regular expressions over the extracted text:

- **Vendor** — a `Vendor:`/`From:` label, else the first non-empty line.
- **Invoice number** — `Invoice #/No/Number: …`, or a standalone `INV-…` token.
- **Date** — a labelled date in several common formats (`YYYY-MM-DD`, `DD/MM/YYYY`, `Month D, YYYY`, …).
- **Currency** — an ISO code (`USD`, `EUR`, …) or a symbol (`$`, `€`, `£`).
- **Total** — `Total` / `Amount Due` / `Grand Total`, explicitly **ignoring** `Subtotal`.
- **Line items** — rows ending in three numeric columns (qty, unit price, amount).

## Testing

```bash
pytest        # 20 tests, all green, no network, no Tesseract
ruff check .  # clean
```

The text-extraction boundary is faked in tests (see `tests/conftest.py`), so the
suite exercises real parsing and validation logic without depending on external
binaries or files.

## Recording the demo GIF

```bash
python examples/make_sample_invoice.py     # writes examples/sample_invoice.pdf
extract-invoice examples/sample_invoice.pdf        # record this running
```

Capture with [ttygif](https://github.com/icholy/ttygif), [asciinema](https://asciinema.org/)
(+ `agg`), [terminalizer](https://github.com/faressoft/terminalizer), or
ScreenToGif on Windows. Save it to `docs/demo.gif` and the link above will resolve.

## Limitations

Rule-based parsing trades some flexibility for being free, offline, and
deterministic. Highly irregular layouts may need their patterns added to
`parser.py`. For very messy or photographed invoices, the boundary is designed
so an alternative `TextExtractor` (or a smarter parser) can be dropped in without
touching the rest of the pipeline.

## License

MIT — see [LICENSE](LICENSE).
