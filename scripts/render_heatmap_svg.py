"""Draw the animated contribution heatmap from data/contributions.json.

Usage:  python scripts/render_heatmap_svg.py
Output: contrib-heatmap.svg
Set STATIC=1 to write a frozen (non-animated) version for previews.
"""
import json
import os
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG, BORDER, DIM = "#0d1117", "#30363d", "#8b949e"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
BOX, GAP = 12, 3
PITCH = BOX + GAP
LEFT, TOP = 44, 46
W = 860

data = json.loads(DATA.read_text(encoding="utf-8"))
days = data["days"]
st = data["stats"]

# place each day in (week column, weekday row); GitHub weeks start on Sunday
first = date.fromisoformat(days[0]["date"])
offset = (first.weekday() + 1) % 7
cells = []
for i, d in enumerate(days):
    pos = i + offset
    cells.append((pos // 7, pos % 7, d))
weeks = cells[-1][0] + 1

grid_bottom = TOP + 7 * PITCH
H = grid_bottom + 56

out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{MONO}" font-size="11">',
    f'<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{BORDER}"/>',
]
if not STATIC:
    out.append(
        "<style>.b{opacity:0;animation:pop .45s ease-out forwards}"
        "@keyframes pop{from{opacity:0;transform:translate(-8px,-8px)}to{opacity:1;transform:translate(0,0)}}</style>"
    )

# month labels (skip a month that only shows up for 1-2 columns at the very start)
last_month, last_x = None, -100
for col, row, d in cells:
    if row != 0:
        continue
    month = date.fromisoformat(d["date"]).strftime("%b")
    if month == last_month:
        continue
    x = LEFT + col * PITCH
    if x - last_x < 3 * PITCH and last_month is not None:
        out.pop()  # the previous label would collide with this one: drop it
    out.append(f'<text x="{x}" y="{TOP - 10}" fill="{DIM}">{month}</text>')
    last_month, last_x = month, x

# weekday labels
for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
    out.append(f'<text x="14" y="{TOP + r * PITCH + BOX - 2}" fill="{DIM}">{name}</text>')

# the boxes
for col, row, d in cells:
    x, y = LEFT + col * PITCH, TOP + row * PITCH
    colour = PALETTE[min(d["level"], len(PALETTE) - 1)]
    title = f'{d["count"]} contributions on {d["date"]}'
    if STATIC:
        out.append(f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" fill="{colour}"><title>{title}</title></rect>')
    else:
        delay = (col + row) * 0.022
        out.append(
            f'<rect class="b" style="animation-delay:{delay:.2f}s" x="{x}" y="{y}" '
            f'width="{BOX}" height="{BOX}" rx="2" fill="{colour}"><title>{title}</title></rect>'
        )

# footer: stats on the left, legend on the right
fy = grid_bottom + 30
out.append(
    f'<text x="{LEFT}" y="{fy}" fill="{DIM}">{st["total"]:,} contributions in the last year'
    f' · current streak {st["current_streak"]}d · longest streak {st["longest_streak"]}d</text>'
)
lx = W - 24 - 5 * (BOX + 4) - 70
out.append(f'<text x="{lx}" y="{fy}" fill="{DIM}">Less</text>')
for i, c in enumerate(PALETTE):
    out.append(f'<rect x="{lx + 34 + i * (BOX + 4)}" y="{fy - 10}" width="{BOX}" height="{BOX}" rx="2" fill="{c}"/>')
out.append(f'<text x="{lx + 34 + 5 * (BOX + 4) + 2}" y="{fy}" fill="{DIM}">More</text>')
out.append("</svg>")
OUT.write_text("\n".join(out), encoding="utf-8")
print(f"Wrote {OUT.name}: {weeks} weeks, {st['total']} contributions")
