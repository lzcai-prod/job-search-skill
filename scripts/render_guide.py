"""Build a single guide.html: Applications, Dashboard (and, in the demo, a CV Portal layout).

Usage: python scripts/render_guide.py profiles/ui-ux out/ranked.json out/guide.html [--open] [--demo]
--demo adds a banner plus sample applications and a sample CV queue from examples/ (layout demo only).
--open launches the page in the default browser. On a machine with no display, such as a cloud
session, it only prints the file path; see SKILL.md for other ways to show it.
The page is static and local. Nothing is uploaded; it contains the user's own data, so
keep it out of public repos (out/ is git-ignored).
"""

import json
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from common import STATUSES, load_profile, tier_of

DEMO_BANNER = (
    '<p class="banner">Design demo with <strong>sample data</strong>. '
    '<a href="https://github.com/lzcai-prod/job-search-skill">Get the skill</a> and ask your AI agent '
    "to run it on your own search.</p>"
)


def read_json(path: Path) -> list:
    return json.loads(path.read_text(encoding="utf-8"))


def page_data(profile: dict, ranked: list[dict], profile_dir: str, demo: bool) -> dict:
    goal = profile.get("goal", {})
    buckets = sorted(profile.get("buckets", {}), key=lambda b: profile["buckets"][b])
    families = [{"name": n, "words": w} for n, w in profile.get("families", {}).items()]
    return {
        "ranked": ranked,
        "companies": [
            {"company": c["company"], "bucket": c.get("bucket", ""), "tier": tier_of(profile, c["company"])}
            for c in profile["companies"]
        ],
        "buckets": buckets,
        "families": families,
        "statuses": STATUSES,
        "profile": {"name": Path(profile_dir).name, "summary": goal.get("summary", "")},
        "demo": demo,
        # sample rows exist only in the demo; a real tracker starts empty
        "seedApps": read_json(ROOT / "examples" / "sample_applications.json") if demo else [],
        "jds": read_json(ROOT / "examples" / "sample_jds.json") if demo else [],
        "framings": ["Auto (from JD)"] + [f["name"] for f in families],
    }


def main(profile_dir: str, ranked_path: str, out_path: str, open_browser: bool = False, demo: bool = False) -> None:
    profile = load_profile(profile_dir)
    ranked = read_json(Path(ranked_path))
    # keep "</script>" out of the embedded JSON
    blob = json.dumps(page_data(profile, ranked, profile_dir, demo)).replace("</", "<\\/")
    page = (ROOT / "templates" / "guide.html").read_text(encoding="utf-8")
    page = page.replace("{{BANNER}}", DEMO_BANNER if demo else "").replace("{{DATA}}", blob)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(page, encoding="utf-8")
    print(f"wrote {Path(out_path).resolve()}", file=sys.stderr)
    if open_browser and not webbrowser.open(Path(out_path).resolve().as_uri()):
        print("could not open a browser; open the file above by hand", file=sys.stderr)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 3:
        sys.exit(__doc__)
    main(*args, open_browser="--open" in sys.argv, demo="--demo" in sys.argv)
