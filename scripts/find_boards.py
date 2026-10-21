"""Detect which public ATS board (Greenhouse, Lever or Ashby) each company uses.

Usage: python scripts/find_boards.py profiles/ui-ux
Probes the public board APIs with guessed slugs and fills the ats and slug columns of
companies.csv for rows that are still blank. Review the result: a guessed slug can hit a
different company with a similar name. One request per second per host.
"""

import csv
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import UA, valid_slug

PROBES = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json&limit=1",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}
_last: dict[str, float] = {}


def candidate_slugs(name: str, hint: str = "") -> list[str]:
    plain = re.sub(r"[^a-z0-9]", "", name.lower())
    dashed = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    seen: list[str] = []
    for s in (hint, plain, dashed):
        if s and valid_slug(s) and s not in seen:
            seen.append(s)
    return seen


def probe(ats: str, slug: str) -> bool:
    url = PROBES[ats].format(slug=slug)
    host = url.split("/")[2]
    wait = 1.0 - (time.monotonic() - _last.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def main(profile_dir: str) -> None:
    path = Path(profile_dir) / "companies.csv"
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        rows = list(reader)
    for row in rows:
        if (row.get("ats") or "").strip() or not row["company"].strip():
            continue
        for slug in candidate_slugs(row["company"]):
            hit = next((a for a in PROBES if probe(a, slug)), None)
            if hit:
                row["ats"], row["slug"] = hit, slug
                print(f"{row['company']}: {hit}/{slug}", file=sys.stderr)
                break
        else:
            print(f"{row['company']}: not found (add ats/slug by hand)", file=sys.stderr)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
