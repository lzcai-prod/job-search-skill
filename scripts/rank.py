"""Produce the top-down ranked list: tier first, then score, then freshness.

Usage: python scripts/rank.py profiles/ui-ux out/postings.json out/ranked.json
Postings below the profile's min_score, or failing its filters, are dropped.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import load_profile, tier_of
from score import passes_filters, score_posting


def rank(postings: list[dict], profile: dict) -> list[dict]:
    min_score = float(profile.get("keywords", {}).get("min_score", 1))
    out = []
    for p in postings:
        if not passes_filters(p, profile):
            continue
        score, reasons = score_posting(p, profile)
        if score < min_score:
            continue
        out.append({**p, "tier": tier_of(profile, p["company"]), "score": score, "reasons": reasons})
    # newest first inside equal tier and score: stable sorts, least significant key first
    out.sort(key=lambda r: str(r.get("posted_at", "")), reverse=True)
    out.sort(key=lambda r: (r["tier"], -r["score"]))
    return out


def main(profile_dir: str, postings_path: str, out_path: str) -> None:
    profile = load_profile(profile_dir)
    postings = json.loads(Path(postings_path).read_text(encoding="utf-8"))
    ranked = rank(postings, profile)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(ranked, indent=2), encoding="utf-8")
    print(f"{len(ranked)} of {len(postings)} postings kept", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
