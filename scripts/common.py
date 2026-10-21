"""Shared helpers: profile loading and the normalised posting shape.

A posting is a dict with: company, title, location, url, description, posted_at, ats.
"""

import csv
import re
import tomllib
from pathlib import Path

SLUG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")
MAX_RESPONSE_BYTES = 10 * 1024 * 1024  # a job-board answer larger than this is not a job board
UA = "job-search-skill/0.1 (personal job posting monitor)"

# The application status ladder: single source for the tracker page and references/data-model.md.
# stage: planned = not sent yet, open = in progress, won = offer, closed = ended.
STATUSES = [
    {"name": "To apply", "stage": "planned"},
    {"name": "Submitted", "stage": "open"},
    {"name": "OA invited", "stage": "open"},
    {"name": "OA done", "stage": "open"},
    {"name": "Interview", "stage": "open"},
    {"name": "Offer", "stage": "won"},
    {"name": "Rejected", "stage": "closed"},
    {"name": "Withdrawn", "stage": "closed"},
]


def valid_slug(slug: str) -> bool:
    """A board slug is one URL path segment: letters, digits, dot, dash, underscore."""
    return bool(SLUG_RE.fullmatch(slug or ""))


def load_profile(profile_dir: str | Path) -> dict:
    """Read profile.toml, keywords.toml and companies.csv from a profile folder."""
    root = Path(profile_dir)
    with (root / "profile.toml").open("rb") as f:
        profile = tomllib.load(f)
    with (root / "keywords.toml").open("rb") as f:
        profile["keywords"] = tomllib.load(f)
    with (root / "companies.csv").open(encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("company") or "").strip()]
    profile["companies"] = rows
    return profile


def tier_of(profile: dict, company: str) -> int:
    """Tier 1 is best. Companies not on the list get the lowest tier."""
    default = int(profile.get("tiers", {}).get("default", 5))
    for row in profile["companies"]:
        if row["company"].strip().lower() == company.strip().lower():
            try:
                return int(row.get("tier") or default)
            except ValueError:
                return default
    return default
