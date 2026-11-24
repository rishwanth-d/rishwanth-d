"""Draw a pattern on your GitHub contribution graph using back-dated empty commits.

Run it INSIDE a separate, dedicated repo (for example "contribution-art"), never inside
your profile repo.  Python's standard library is all it needs.

Examples (from inside the contribution-art folder):
    python path/to/contribution_art.py --text RISH --email you@example.com --dry-run
    python path/to/contribution_art.py --text RISH --email you@example.com
    python path/to/contribution_art.py --pattern mypattern.txt --email you@example.com

Fill the whole graph:
    python path/to/contribution_art.py --text RISZ --gap 2 --background 1 --email you@example.com
    python path/to/contribution_art.py --demo wave --email you@example.com
(demos: wave, double, zigzag, tide, mountains, heartbeat, checker, gradient, stripes)

--email must be an email that is VERIFIED on your GitHub account, or the commits
will not count.

A pattern file has exactly 7 lines (Sunday to Saturday), one character per week:
    .  = empty        1 2 3 4 = lightest .. darkest green
"""
import argparse
import math
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone

COLS = 53
COMMITS_PER_LEVEL = {1: 1, 2: 2, 3: 4, 4: 6}  # roughly the quartiles GitHub uses

FONT = {
"A": [".###.","#...#","#...#","#####","#...#","#...#","#...#"],
"B": ["####.","#...#","#...#","####.","#...#","#...#","####."],
"C": [".###.","#...#","#....","#....","#....","#...#",".###."],
"D": ["####.","#...#","#...#","#...#","#...#","#...#","####."],
"E": ["#####","#....","#....","####.","#....","#....","#####"],
"F": ["#####","#....","#....","####.","#....","#....","#...."],
"G": [".###.","#...#","#....","#.###","#...#","#...#",".###."],
"H": ["#...#","#...#","#...#","#####","#...#","#...#","#...#"],
"I": ["#####","..#..","..#..","..#..","..#..","..#..","#####"],
"J": ["..###","...#.","...#.","...#.","...#.","#..#.",".##.."],
"K": ["#...#","#..#.","#.#..","##...","#.#..","#..#.","#...#"],
"L": ["#....","#....","#....","#....","#....","#....","#####"],
"M": ["#...#","##.##","#.#.#","#.#.#","#...#","#...#","#...#"],
"N": ["#...#","##..#","#.#.#","#..##","#...#","#...#","#...#"],
"O": [".###.","#...#","#...#","#...#","#...#","#...#",".###."],
"P": ["####.","#...#","#...#","####.","#....","#....","#...."],
"Q": [".###.","#...#","#...#","#...#","#.#.#","#..#.",".##.#"],
"R": ["####.","#...#","#...#","####.","#.#..","#..#.","#...#"],
"S": [".####","#....","#....",".###.","....#","....#","####."],
"T": ["#####","..#..","..#..","..#..","..#..","..#..","..#.."],
"U": ["#...#","#...#","#...#","#...#","#...#","#...#",".###."],
"V": ["#...#","#...#","#...#","#...#","#...#",".#.#.","..#.."],
"W": ["#...#","#...#","#...#","#.#.#","#.#.#","##.##","#...#"],
"X": ["#...#","#...#",".#.#.","..#..",".#.#.","#...#","#...#"],
"Y": ["#...#","#...#",".#.#.","..#..","..#..","..#..","..#.."],
"Z": ["#####","....#","...#.","..#..",".#...","#....","#####"],
"0": [".###.","#...#","#..##","#.#.#","##..#","#...#",".###."],
"1": ["..#..",".##..","..#..","..#..","..#..","..#..",".###."],
"2": [".###.","#...#","....#","...#.","..#..",".#...","#####"],
"3": ["####.","....#","....#",".###.","....#","....#","####."],
"4": ["...#.","..##.",".#.#.","#..#.","#####","...#.","...#."],
"5": ["#####","#....","####.","....#","....#","#...#",".###."],
"6": ["..##.",".#...","#....","####.","#...#","#...#",".###."],
"7": ["#####","....#","...#.","..#..",".#...",".#...",".#..."],
"8": [".###.","#...#","#...#",".###.","#...#","#...#",".###."],
"9": [".###.","#...#","#...#",".####","....#","...#.",".##.."],
"*": [".##.##.","#######","#######",".#####.","..###..","...#...","......."],  # heart
"^": ["...#...","..###..","#######",".#####.","..###..",".##.##.",".#...#."],  # star
"~": ["...##","..##.",".##..","#####","..##.",".##..","##..."],  # lightning bolt
"<": ["...#.","..#..",".#...","#....",".#...","..#..","...#."],
">": [".#...","..#..","...#.","....#","...#.","..#..",".#..."],
"/": ["....#","....#","...#.","..#..",".#...","#....","#...."],
" ": ["...","...","...","...","...","...","..."],
}


def text_to_grid(text, level, gap=1):
    glyphs = []
    for ch in text.upper():
        if ch not in FONT:
            sys.exit(f"Character {ch!r} is not available. Use letters, digits, space, or the symbols * (heart) ^ (star) ~ (bolt) < > /.")
        glyphs.append(FONT[ch])
    rows = []
    for r in range(7):
        parts = ["".join(str(level) if c == "#" else "." for c in g[r]) for g in glyphs]
        rows.append(("." * gap).join(parts))  # blank columns between characters
    return rows


DEMOS = ["wave", "double", "zigzag", "tide", "mountains", "heartbeat", "checker", "gradient", "stripes"]


def demo_grid(name):
    g = [[0] * COLS for _ in range(7)]

    def put(r, c, lvl):
        if 0 <= r < 7 and g[r][c] < lvl:
            g[r][c] = lvl

    def band(c, centre, thin=False):  # a line: bright core, fading shades around it
        for r in range(7):
            d = abs(r - centre)
            if thin:
                put(r, c, 4 if d < 0.6 else 2 if d < 1.2 else 0)
            else:
                put(r, c, 4 if d < 0.7 else 3 if d < 1.5 else 2 if d < 2.3 else 1 if d < 3.2 else 0)

    ecg = [3, 3, 3, 3, 2, 2, 3, 3, 0, 6, 3, 3, 3, 3, 3, 3]
    for c in range(COLS):
        if name == "wave":
            band(c, 3 + 3 * math.sin(c / COLS * 4 * math.pi))
        elif name == "double":
            band(c, 3 + 2.8 * math.sin(c / COLS * 4 * math.pi), thin=True)
            band(c, 3 + 2.8 * math.sin(c / COLS * 4 * math.pi + math.pi), thin=True)
        elif name == "zigzag":
            t = (c % 10) / 10
            band(c, 6 * (1 - abs(2 * t - 1)))
        elif name == "tide":
            surf = 2 + 1.6 * math.sin(c / COLS * 4 * math.pi)
            for r in range(7):
                if r >= surf - 0.5:
                    depth = max(0.0, r - surf)
                    put(r, c, 4 if depth < 0.8 else 3 if depth < 1.8 else 2 if depth < 3 else 1)
        elif name == "mountains":
            h = 3.5 + 2.2 * math.sin(c * 0.35) + 1.4 * math.sin(c * 0.9 + 1)
            top = 7 - max(1, min(7, round(h)))
            for r in range(top, 7):
                put(r, c, {0: 4, 1: 3, 2: 2}.get(r - top, 1))
        elif name == "heartbeat":
            y0, y1 = ecg[c % len(ecg)], ecg[(c + 1) % len(ecg)]
            step = 1 if y1 >= y0 else -1
            for r in range(y0, y1 if y1 != y0 else y0 + 1, step):
                put(r, c, 4)
        else:
            for r in range(7):
                if name == "checker":
                    put(r, c, 4 if (r + c) % 2 == 0 else 2)
                elif name == "gradient":
                    put(r, c, min(4, 1 + c * 4 // COLS))
                else:  # stripes
                    put(r, c, ((c + r) // 2) % 4 + 1)
    return ["".join(str(v) if v else "." for v in row) for row in g]


def add_background(rows, col0, level):
    """Fill every empty cell of the full 53-week grid with `level`, keeping the pattern on top."""
    full = [[str(level)] * COLS for _ in range(7)]
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch not in ".0":
                full[r][col0 + c] = ch
    return ["".join(row) for row in full]


def read_pattern(path):
    with open(path, encoding="utf-8") as f:
        rows = [ln.strip() for ln in f if ln.strip()]
    if len(rows) != 7:
        sys.exit(f"The pattern file needs exactly 7 lines (it has {len(rows)}).")
    width = max(len(r) for r in rows)
    rows = [r.ljust(width, ".") for r in rows]
    for r in rows:
        for c in r:
            if c not in ".01234":
                sys.exit(f"Bad character {c!r} in the pattern. Use . and 1-4 only.")
    return rows


def plan(rows, today, col0):
    last_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
    start = last_sunday - timedelta(weeks=COLS - 1)
    jobs = []  # (date, commits)
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch in ".0":
                continue
            d = start + timedelta(days=(col0 + c) * 7 + r)
            if d <= today:
                jobs.append((d, COMMITS_PER_LEVEL[int(ch)]))
    return start, sorted(jobs)


def show(rows, col0):
    print("Preview (. = empty, 1-4 = shade). Each line is a weekday, Sunday first:\n")
    pad = "." * col0
    for name, line in zip(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], rows):
        print(f"  {name}  {(pad + line).ljust(COLS, '.')}")
    print()


def git(*args, env=None, check=True):
    return subprocess.run(["git", *args], env=env, check=check, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", help="word to write, e.g. RISH (letters, digits, space; symbols: * heart, ^ star, ~ bolt, < > /)")
    src.add_argument("--pattern", help="path to a 7-line pattern file")
    src.add_argument("--demo", choices=DEMOS, help="a ready-made full-graph pattern")
    ap.add_argument("--email", required=True, help="an email VERIFIED on your GitHub account")
    ap.add_argument("--name", default="Rishwanth D", help="author name for the commits")
    ap.add_argument("--user", default="rishwanth-d", help="your GitHub username (safety check)")
    ap.add_argument("--level", type=int, default=4, choices=[1, 2, 3, 4], help="shade for --text (default 4)")
    ap.add_argument("--gap", type=int, default=1, choices=[1, 2, 3, 4], help="blank columns between letters (default 1)")
    ap.add_argument("--background", type=int, choices=[1, 2, 3], default=0,
                    help="fill every other square with this shade so the whole graph is full")
    ap.add_argument("--col", type=int, default=None, help="start column 0-52 (default: centred)")
    ap.add_argument("--dry-run", action="store_true", help="only show the preview, create nothing")
    ap.add_argument("--force", action="store_true", help="skip the profile-repo safety check")
    a = ap.parse_args()

    if a.demo:
        rows = demo_grid(a.demo)
    else:
        rows = text_to_grid(a.text, a.level, a.gap) if a.text else read_pattern(a.pattern)
    width = len(rows[0])
    if width > COLS:
        sys.exit(f"The pattern is {width} columns wide but the graph only has {COLS}. Use a shorter word.")
    col0 = a.col if a.col is not None else (COLS - width) // 2
    col0 = max(0, min(col0, COLS - width))
    if a.background:
        rows, col0 = add_background(rows, col0, a.background), 0

    today = datetime.now(timezone.utc).date()
    _, jobs = plan(rows, today, col0)
    total = sum(n for _, n in jobs)
    show(rows, col0)
    print(f"This will create {total} empty commits on {len(jobs)} different days.")
    if a.dry_run:
        print("Dry run only: nothing was created.")
        return

    # Safety checks
    if git("rev-parse", "--is-inside-work-tree", check=False).returncode != 0:
        sys.exit("This folder is not a git repo. cd into your contribution-art folder first.")
    remote = git("remote", "get-url", "origin", check=False).stdout.strip().lower()
    if remote.rstrip("/").removesuffix(".git").split("/")[-1] == a.user.lower() and not a.force:
        sys.exit("This looks like your PROFILE repo. Run this in a separate repo (contribution-art).")
    if input("Type yes to create the commits: ").strip().lower() != "yes":
        sys.exit("Cancelled.")

    done = 0
    for d, n in jobs:
        stamp = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")
        env = dict(os.environ, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        for i in range(n):
            git("-c", f"user.name={a.name}", "-c", f"user.email={a.email}",
                "commit", "--allow-empty", "-q", "-m", f"art {d.isoformat()} #{i + 1}", env=env)
            done += 1
        print(f"\r{done}/{total} commits", end="", flush=True)
    print("\nDone. Now run:  git push")


if __name__ == "__main__":
    main()
