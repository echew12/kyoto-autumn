"""Read Keihan's autumn-leaves report and save our three spots to foliage.json.

Runs on GitHub Actions. If anything about the page looks unexpected, it leaves
foliage.json alone, so the site never shows a wrong status, only an old one.
Standard library only, so the workflow needs no installs.
"""
import html
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.keihan.co.jp/momiji/index_en.html"
OUT = Path(__file__).resolve().parent.parent / "foliage.json"

# our key -> the name Keihan uses
SPOTS = {"kodaiji": "Kodaiji Temple", "shinnyodo": "Shinnyodo Temple", "nanzenji": "Nanzenji Temple"}

# Keihan's labels -> the page's stage index (0 green ... 4 fallen).
# Longer labels first so "Past the peak" is not read as "Peak".
LABELS = [
    ("past the peak", 3), ("past peak", 3),
    ("changing colors", 1), ("changing colours", 1),
    ("green leaves", 0), ("fallen leaves", 4),
    ("peak", 2),
]
LABEL_RE = re.compile("|".join(re.escape(l) for l, _ in LABELS), re.I)
LABEL_TO_STAGE = {l: s for l, s in LABELS}
WINDOW = 160  # how far after a spot's name its status may appear, in characters
# every spot on Keihan's list, so a match never borrows the next spot's status
ALL_SPOTS_RE = re.compile(
    r"Arashiyama|Togetsukyo|Eikando|Kitano|Kodaiji|Sanzen-?in|Shinnyodo|Sennyuji|Tofukuji|"
    r"Nanzenji|Bishamondo|Honen-?in|Hiyoshi", re.I)


def page_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)  # drops tags and their alt text
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def parse(text: str) -> dict:
    m = re.search(r"as of\s+([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})", text, re.I)
    if not m:
        raise ValueError("could not find the 'as of' date")
    as_of = datetime.strptime(f"{m.group(1)} {int(m.group(2))} {m.group(3)}", "%B %d %Y").date().isoformat()

    spots = {}
    for key, name in SPOTS.items():
        found = None
        for hit in re.finditer(re.escape(name), text, re.I):
            after = text[hit.end(): hit.end() + WINDOW]
            # the next spot's name must not come before the label
            nxt = ALL_SPOTS_RE.search(after)
            lab = LABEL_RE.search(after)
            if lab and (not nxt or lab.start() < nxt.start()):
                found = LABEL_TO_STAGE[lab.group(0).lower()]
                break
        if found is None:
            raise ValueError(f"could not find a status for {name}")
        spots[key] = found
    return {"asOf": as_of, "spots": spots}


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": "kyoto-momiji-site/1.0 (+GitHub Actions)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")
        new = parse(page_text(raw))
    except Exception as e:  # keep the old file on any problem
        print(f"::warning::Keihan check skipped, keeping the current foliage.json ({e})")
        return 0

    old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
    if old.get("asOf", "") > new["asOf"]:
        print(f"::warning::Keihan date {new['asOf']} is older than saved {old['asOf']}; keeping saved data")
        return 0
    if old.get("asOf") == new["asOf"] and old.get("spots") == new["spots"]:
        print(f"No change (as of {new['asOf']}): {new['spots']}")
        return 0

    new["source"] = URL
    new["checked"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    OUT.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"Updated foliage.json (as of {new['asOf']}): {new['spots']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
