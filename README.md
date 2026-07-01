# 🧾 invoice-extractor

**Extract structured data from invoice PDFs and images — offline and rule-based by default, or LLM-driven with Claude.**

Point it at a `.pdf`, `.png`, or `.jpg` invoice and get back a validated `Invoice`
object (vendor, invoice number, date, currency, total, line items) as a typed
Python object, a table, or JSON.

Two interchangeable parsing backends behind one interface:

- **Offline (default)** — deterministic regex rules. No API key, no network, zero token cost.
- **LLM (`--llm`)** — Claude turns the extracted text into structured data, for messy or irregular layouts the rules don't cover.

Both paths return the same schema-validated `Invoice` and run through the same
coherence checks.

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

![demo — extract-invoice running on a sample invoice](docs/demo.gif)

---

## Why this design

- **Offline by default: no API keys, no network, no per-token cost.** Text is
  pulled locally (`pdfplumber` for PDFs, Tesseract OCR for images) and parsed
  with deterministic rules. The same input always produces the same output.
- **Two clean, testable boundaries.** The two parts that touch the outside world
  — reading file bytes into text (`TextExtractor`) and calling the model
  (`LLMClient`) — each sit behind a small protocol. Tests inject fakes, so the
  suite runs in milliseconds with **no PDFs, no Tesseract, no API key, and no
  network**. The LLM's *reliability* isn't tested; the parsing, validation, and
  routing *logic* around it is — which is what a reviewer actually wants to see.
- **The API key is never hardcoded.** The Claude client reads it from the
  `ANTHROPIC_API_KEY` environment variable, and nothing else in the codebase
  touches secrets (R7).
- **Schema-validated output, whichever backend ran.** Results are
  [Pydantic](https://docs.pydantic.dev/) models, and the line-item amounts must
  reconcile with the invoice total — even the LLM's output — or you get a clear
  `InvoiceValidationError`.

## Features

| | |
|---|---|
| **R1** | Accept a `.pdf` / `.png` / `.jpg` path → return a validated `Invoice`. |
| **R2** | `Invoice` schema: `vendor`, `invoice_number`, `date`, `currency`, `total` (`Decimal`), `line_items`. |
| **R3** | Both the text extractor and the LLM call sit behind protocols (`TextExtractor`, `LLMClient`) → trivially mockable. |
| **R4** | Coherence check: line items must sum to `total` (±0.01) or raise `InvoiceValidationError` — applies to both backends. |
| **R5** | CLI: `extract-invoice <file> [--json] [--llm]` prints a table or JSON. |
| **R6** | Graceful, typed errors: missing file, unsupported format, unreadable text, unparseable content, unparseable LLM output (`LLMResponseError`). |
| **R7** | The Claude API key is read from `ANTHROPIC_API_KEY`, never hardcoded. |

## Architecture

```
            ┌────────────────────────────────────────────────────────┐
file path → │  extractor.extract_invoice(path, extractor?, llm?)     │
            │    1. validate path + format                           │
            │    2. TextExtractor.extract_text()   ◄── boundary (mocked in tests)
            │    3. parse the text into an Invoice:                  │
            │         • llm is None → parser.parse_invoice()  (offline rules)
            │         • llm given   → llm.parse_invoice_with_llm(client)
            │           └ LLMClient.complete()    ◄── boundary (mocked in tests)
            │    4. validation.validate_totals()                     │
            └────────────────────────────────────────────────────────┘ → Invoice (Pydantic)
```

```
src/invoice_extractor/
├─ models.py            # Invoice, LineItem (Pydantic)
├─ text_extraction.py   # TextExtractor protocol + LocalTextExtractor (pdfplumber / Tesseract)
├─ parser.py            # parse_invoice(text) -> Invoice   ← the offline rule engine
├─ llm.py               # LLMClient protocol + AnthropicClient + parse_invoice_with_llm()
├─ extractor.py         # extract_invoice(path, extractor, llm) -> Invoice
├─ validation.py        # validate_totals()
└─ cli.py               # extract-invoice <file> [--json] [--llm]
```

## Install

```bash
python -m pip install -e ".[dev]"
```

For the optional **LLM backend** (`--llm`), also install the Anthropic SDK and
set your API key:

```bash
python -m pip install -e ".[llm]"
export ANTHROPIC_API_KEY=sk-ant-...     # Windows: setx ANTHROPIC_API_KEY sk-ant-...
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
extract-invoice path/to/invoice.pdf            # human-readable table (offline rules)
extract-invoice path/to/invoice.pdf --json     # JSON
extract-invoice path/to/invoice.pdf --llm       # parse with Claude (needs ANTHROPIC_API_KEY)
extract-invoice path/to/invoice.pdf --llm --json
```

### As a library

```python
from invoice_extractor import extract_invoice

# Offline, rule-based (default)
invoice = extract_invoice("invoice.pdf")
print(invoice.vendor, invoice.total)
for item in invoice.line_items:
    print(item.description, item.amount)

# LLM-driven with Claude
from invoice_extractor import AnthropicClient
invoice = extract_invoice("invoice.pdf", llm=AnthropicClient())
```

Need to test your own pipeline without files or API calls? Inject fakes at either
boundary — any object with an `extract_text(*, file_bytes, media_type) -> str`
method, and/or a `complete(*, prompt) -> str` method:

```python
class MyExtractor:
    def extract_text(self, *, file_bytes, media_type):
        return "Acme Corp\nInvoice #: INV-1\nDate: 2026-06-01\nTotal: 100.00\n"

class MyLLM:
    def complete(self, *, prompt):
        return '{"vendor": "Acme Corp", "invoice_number": "INV-1", ...}'

extract_invoice("invoice.pdf", MyExtractor())              # offline
extract_invoice("invoice.pdf", MyExtractor(), MyLLM())     # LLM path, fully mocked
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

## How the LLM path works

With `--llm` (or `extract_invoice(..., llm=AnthropicClient())`), the same
extracted text is sent to Claude (`claude-opus-4-8`) with a system prompt that
pins the exact JSON shape to return. `parse_invoice_with_llm()` strips any code
fences, parses the JSON, and validates it against the `Invoice` schema —
raising `LLMResponseError` (a subclass of `ParsingError`) if the model returns
non-JSON or an off-schema object. The result then goes through the **same**
`validate_totals()` check as the offline path, so a hallucinated total that
doesn't reconcile with the line items is still caught.

The model call lives entirely inside `AnthropicClient.complete()` behind the
`LLMClient` protocol, so the parsing and validation logic is unit-tested with a
fake that returns canned JSON — no API key, no network, no token cost.

## Testing

```bash
pytest        # 27 tests, all green, no network, no Tesseract, no API key
ruff check .  # clean
```

Both boundaries — text extraction and the LLM call — are faked in tests (see
`tests/conftest.py`), so the suite exercises real parsing and validation logic
without depending on external binaries, files, or a live API.

## Regenerating the demo GIF

The GIF above (`docs/demo.gif`) is rendered from the tool's real, deterministic
output — regenerate it any time with:

```bash
python examples/make_sample_invoice.py     # writes examples/sample_invoice.pdf
python docs/make_demo_gif.py               # writes docs/demo.gif
```

`docs/make_demo_gif.py` uses Pillow (already a dependency) — no screen-capture
tooling needed. Prefer a real terminal capture? [asciinema](https://asciinema.org/)
(+ `agg`), [ttygif](https://github.com/icholy/ttygif), or ScreenToGif on Windows
all work; just save the result to `docs/demo.gif`.

## Limitations

Rule-based parsing trades some flexibility for being free, offline, and
deterministic. Highly irregular layouts may need their patterns added to
`parser.py` — or you can reach for `--llm`, which handles messy layouts at the
cost of an API call and per-token pricing. The `LLMClient` protocol means any
other provider can be adapted behind the same interface without touching the
rest of the pipeline.

## License

MIT — see [LICENSE](LICENSE).
