"""Fetch postings from public Greenhouse, Lever and Ashby job-board APIs.

Usage: python scripts/fetch_board.py profiles/ui-ux out/postings.json
Reads the profile's companies.csv (columns: company, ats, slug) and writes normalised postings.
Rows without ats/slug are skipped; run find_boards.py first to fill them in.
One request per second per host. Only public, unauthenticated endpoints are used.
"""

import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import UA, load_profile

URLS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{slug}?mode=json",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}
_last: dict[str, float] = {}


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text or ""))).strip()


def parse_greenhouse(company: str, data: dict) -> list[dict]:
    return [
        {
            "company": company,
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "description": strip_html(j.get("content", "")),
            "posted_at": j.get("updated_at") or j.get("first_published") or "",
            "ats": "greenhouse",
        }
        for j in data.get("jobs", [])
    ]


def parse_lever(company: str, data: list) -> list[dict]:
    return [
        {
            "company": company,
            "title": j.get("text", ""),
            "location": (j.get("categories") or {}).get("location", "") or "",
            "url": j.get("hostedUrl", ""),
            "description": j.get("descriptionPlain", "") or strip_html(j.get("description", "")),
            "posted_at": str(j.get("createdAt", "")),
            "ats": "lever",
        }
        for j in data
    ]


def parse_ashby(company: str, data: dict) -> list[dict]:
    return [
        {
            "company": company,
            "title": j.get("title", ""),
            "location": j.get("location", "") or "",
            "url": j.get("jobUrl", ""),
            "description": j.get("descriptionPlain", "") or strip_html(j.get("descriptionHtml", "")),
            "posted_at": j.get("publishedAt", "") or "",
            "ats": "ashby",
        }
        for j in data.get("jobs", [])
    ]


PARSERS = {"greenhouse": parse_greenhouse, "lever": parse_lever, "ashby": parse_ashby}


def get_json(url: str):
    host = url.split("/")[2]
    wait = 1.0 - (time.monotonic() - _last.get(host, 0.0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch(company: str, ats: str, slug: str) -> list[dict]:
    return PARSERS[ats](company, get_json(URLS[ats].format(slug=slug)))


def main(profile_dir: str, out_path: str) -> None:
    profile = load_profile(profile_dir)
    postings: list[dict] = []
    for row in profile["companies"]:
        ats, slug = (row.get("ats") or "").strip(), (row.get("slug") or "").strip()
        if ats not in PARSERS or not slug:
            continue
        try:
            found = fetch(row["company"], ats, slug)
        except (OSError, ValueError, KeyError) as exc:  # one broken board must not stop the sweep
            print(f"skip {row['company']}: {exc}", file=sys.stderr)
            continue
        print(f"{row['company']}: {len(found)} postings", file=sys.stderr)
        postings.extend(found)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(postings, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
