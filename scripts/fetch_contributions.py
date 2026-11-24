"""Download your public contribution calendar (no token needed).

Usage:  python scripts/fetch_contributions.py
Output: data/contributions.json
"""
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USER = os.environ.get("GITHUB_USER", "rishwanth-d")
URL = f"https://github.com/users/{USER}/contributions"


def level_from_count(n):
    if n <= 0:
        return 0
    if n <= 2:
        return 1
    if n <= 5:
        return 2
    if n <= 9:
        return 3
    return 4


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    # Counts live in <tool-tip for="<cell id>">3 contributions on ...</tool-tip>
    tips = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"\s*(No|\d[\d,]*)\s+contribution", tip.get_text())
        if m and tip.get("for"):
            tips[tip["for"]] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))

    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        d = cell["data-date"]
        count = tips.get(cell.get("id"))
        if count is None:  # fall back to the cell's own text, if any
            m = re.search(r"(\d[\d,]*)\s+contribution", cell.get_text())
            count = int(m.group(1).replace(",", "")) if m else None
        if count is None:
            count = 0 if cell.get("data-level", "0") == "0" else 1
        level = int(cell.get("data-level", level_from_count(count)))
        days.append({"date": d, "count": count, "level": level})
    days.sort(key=lambda x: x["date"])
    return days


def stats(days):
    total = sum(d["count"] for d in days)
    by_date = {d["date"]: d["count"] for d in days}
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    # current streak: count back from today (or yesterday if today is empty)
    cur = 0
    if days:
        day = date.fromisoformat(days[-1]["date"])
        if by_date.get(day.isoformat(), 0) == 0:
            day -= timedelta(days=1)
        while by_date.get(day.isoformat(), 0) > 0:
            cur += 1
            day -= timedelta(days=1)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    return {
        "total": total,
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": months,
    }


if __name__ == "__main__":
    resp = requests.get(URL, headers={"User-Agent": "profile-readme-bot"}, timeout=30)
    resp.raise_for_status()
    days = parse(resp.text)
    if not days:
        raise SystemExit("Could not find the contribution calendar in GitHub's response.")
    OUT.parent.mkdir(exist_ok=True)
    data = {"user": USER, "days": days, "stats": stats(days)}
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"Saved {len(days)} days, {data['stats']['total']} contributions -> {OUT}")
