"""Build the neofetch-style info card.

Usage:  python scripts/make_info_card.py
Output: info-card.svg
Edit the ROWS list below whenever you want to change what the card says.
Set STATIC=1 to write a frozen version for previews.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# ---- EDIT ME ---------------------------------------------------------------
TITLE = "rishwanth@github"
ROWS = [
    ("Name", "Rishwanth D"),
    ("Now", "BE CSE, 1st year"),
    ("Uni", "Rajalakshmi Institute of Technology"),
    ("Learning", "C · Python · Git"),
    ("Focus", "Programming · Problem-solving · AI"),
    ("Goal", "Build meaningful solutions with tech"),
    ("Mail", "rishwanth.dilli@gmail.com"),
    ("LinkedIn", "linkedin.com/in/rishwanth-d-4b2ab1440"),
]
# -----------------------------------------------------------------------------

W = 490
LINE_H = 24
TOP = 74
H = max(TOP + len(ROWS) * LINE_H + 26, 300)
BG, BORDER, BAR = "#0d1117", "#30363d", "#161b22"
KEY, VAL, DIM = "#39d353", "#c9d1d9", "#8b949e"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"

def reveal(delay):
    """Fade + slide-in animation children for one line."""
    if STATIC:
        return ""
    return (
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="-10 0" to="0 0" '
        f'begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
    )

op = "1" if STATIC else "0"
out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{MONO}" font-size="13">',
    f'<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
    f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v26H0z" fill="{BAR}"/>',
    '<circle cx="22" cy="18" r="5.5" fill="#ff5f56"/><circle cx="42" cy="18" r="5.5" fill="#ffbd2e"/><circle cx="62" cy="18" r="5.5" fill="#27c93f"/>',
    f'<text x="{W // 2}" y="22" text-anchor="middle" fill="{DIM}" font-size="12">{escape(TITLE)}</text>',
]

# prompt line
out.append(
    f'<g opacity="{op}"><text x="24" y="58" fill="{DIM}">$ neofetch</text>{reveal(0.3)}</g>'
)
for i, (k, v) in enumerate(ROWS):
    y = TOP + 14 + i * LINE_H
    d = 0.7 + i * 0.25
    out.append(
        f'<g opacity="{op}">'
        f'<text x="24" y="{y}" fill="{KEY}" font-weight="bold">{escape(k)}</text>'
        f'<text x="104" y="{y}" fill="{DIM}">:</text>'
        f'<text x="120" y="{y}" fill="{VAL}">{escape(v)}</text>'
        f"{reveal(d)}</g>"
    )

# colour swatches, like neofetch
sw_y = TOP + 14 + len(ROWS) * LINE_H - 6
colors = ["#ff5f56", "#ffbd2e", "#27c93f", "#39d353", "#58a6ff", "#bc8cff", "#c9d1d9"]
sw = "".join(f'<rect x="{24 + j * 22}" y="{sw_y}" width="18" height="10" rx="2" fill="{c}"/>' for j, c in enumerate(colors))
out.append(f'<g opacity="{op}">{sw}{reveal(0.7 + len(ROWS) * 0.25)}</g>')
out.append("</svg>")
OUT.write_text("\n".join(out), encoding="utf-8")
print(f"Wrote {OUT.name}")
