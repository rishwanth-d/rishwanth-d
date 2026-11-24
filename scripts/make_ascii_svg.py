"""Step 2 of the portrait: turn source-prepped.png into a self-typing ASCII SVG.

Usage:  python scripts/make_ascii_svg.py
Output: rishwanth-ascii.svg
Set STATIC=1 to write a frozen (non-animated) version for previews.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "rishwanth-ascii.svg"
STATIC = os.environ.get("STATIC") == "1"

COLS = 100
CHAR_W, CHAR_H = 6, 10          # size of one character cell in SVG units
PAD = 20
RAMP = " .`:-=+*cs#%@"          # bright (sparse) -> dark (dense)
FILL = "#c9d1d9"
BG, BORDER = "#0d1117", "#30363d"
ROW_DELAY, WIPE = 0.07, 0.55    # seconds

img = Image.open(SRC).convert("L")
w, h = img.size
rows = max(1, round(h / w * COLS * (CHAR_W / CHAR_H)))
small = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255.0
small = small ** 1.4            # nudge highlights toward blank for a cleaner look

lines = []
for r in range(rows):
    idx = ((1.0 - small[r]) * (len(RAMP) - 1)).round().astype(int)
    lines.append("".join(RAMP[i] for i in idx))

W = COLS * CHAR_W + PAD * 2
H = rows * CHAR_H + PAD * 2
text_w = COLS * CHAR_W

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
    f'<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
]

defs = []
body = []
for i, line in enumerate(lines):
    y = PAD + (i + 1) * CHAR_H - 2
    t0 = i * ROW_DELAY
    text = (
        f'<text x="{PAD}" y="{y}" fill="{FILL}" font-size="{CHAR_H}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'DejaVu Sans Mono\',monospace" '
        f'xml:space="preserve" textLength="{text_w}" lengthAdjust="spacingAndGlyphs">{escape(line)}</text>'
    )
    if STATIC:
        body.append(text)
        continue
    defs.append(
        f'<clipPath id="c{i}"><rect x="{PAD}" y="{y - CHAR_H}" width="0" height="{CHAR_H + 2}">'
        f'<animate attributeName="width" from="0" to="{text_w}" begin="{t0:.2f}s" dur="{WIPE}s" fill="freeze"/>'
        f"</rect></clipPath>"
    )
    body.append(f'<g clip-path="url(#c{i})">{text}</g>')
    # small block "cursor" riding the wipe edge, then vanishing
    body.append(
        f'<rect x="{PAD}" y="{y - CHAR_H + 1}" width="{CHAR_W}" height="{CHAR_H}" fill="{FILL}" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{t0:.2f}s"/>'
        f'<animate attributeName="x" from="{PAD}" to="{PAD + text_w}" begin="{t0:.2f}s" dur="{WIPE}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0" begin="{t0 + WIPE:.2f}s"/>'
        f"</rect>"
    )

if defs:
    parts.append("<defs>" + "".join(defs) + "</defs>")
parts += body
parts.append("</svg>")
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"Wrote {OUT.name}: {COLS}x{rows} characters, {OUT.stat().st_size // 1024} KB")
