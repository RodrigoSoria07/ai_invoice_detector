"""Render a terminal-style demo GIF of the CLI, using the tool's *real* output.

The output text below is copied verbatim from:

    extract-invoice examples/sample_invoice.pdf --json

Since extraction is offline and deterministic, this is faithful to a real run —
it's just rendered as a terminal animation instead of screen-captured. Run:

    python docs/make_demo_gif.py     # writes docs/demo.gif

Requires Pillow (already a dependency of the project).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# --- the real command + output ------------------------------------------------

PROMPT = "$ "
COMMAND = "extract-invoice examples/sample_invoice.pdf --json"
OUTPUT = """\
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
}""".splitlines()

# --- terminal look ------------------------------------------------------------

BG = (30, 30, 46)
PROMPT_COLOR = (137, 220, 235)
CMD_COLOR = (166, 227, 161)
OUT_COLOR = (205, 214, 244)
PUNCT_COLOR = (147, 153, 178)

FONT_SIZE = 18
PAD = 20
LINE_H = FONT_SIZE + 6


def _load_font() -> ImageFont.FreeTypeFont:
    for name in ("consola.ttf", "cour.ttf", "DejaVuSansMono.ttf", "Menlo.ttc"):
        try:
            return ImageFont.truetype(name, FONT_SIZE)
        except OSError:
            continue
    return ImageFont.load_default()


FONT = _load_font()


def _canvas_size() -> tuple[int, int]:
    longest = max([PROMPT + COMMAND, *OUTPUT], key=len)
    width = int(FONT.getlength(longest)) + PAD * 2
    height = (len(OUTPUT) + 2) * LINE_H + PAD * 2
    return width, height


WIDTH, HEIGHT = _canvas_size()


def _color_for(line: str) -> tuple[int, int, int]:
    return PUNCT_COLOR if line.strip() in {"{", "}", "],", "]"} else OUT_COLOR


def _frame(command_shown: str, output_lines: int, cursor: bool) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    y = PAD

    draw.text((PAD, y), PROMPT, font=FONT, fill=PROMPT_COLOR)
    x = PAD + FONT.getlength(PROMPT)
    draw.text((x, y), command_shown, font=FONT, fill=CMD_COLOR)
    if cursor:
        cx = x + FONT.getlength(command_shown)
        draw.text((cx, y), "█", font=FONT, fill=CMD_COLOR)
    y += LINE_H * 2

    for line in OUTPUT[:output_lines]:
        draw.text((PAD, y), line, font=FONT, fill=_color_for(line))
        y += LINE_H

    return img


def build() -> None:
    frames: list[Image.Image] = []
    durations: list[int] = []

    # 1. Type the command, a few characters at a time.
    for i in range(0, len(COMMAND) + 1, 3):
        frames.append(_frame(COMMAND[:i], 0, cursor=True))
        durations.append(45)

    # 2. Brief pause on the full command (blinking cursor).
    for cursor in (True, False, True):
        frames.append(_frame(COMMAND, 0, cursor=cursor))
        durations.append(350)

    # 3. Reveal output line by line.
    for n in range(1, len(OUTPUT) + 1):
        frames.append(_frame(COMMAND, n, cursor=False))
        durations.append(140)

    # 4. Hold the final frame.
    frames.append(_frame(COMMAND, len(OUTPUT), cursor=False))
    durations.append(2600)

    out = Path(__file__).parent / "demo.gif"
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {out} ({len(frames)} frames, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    build()
