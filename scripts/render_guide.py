"""Build a single guide.html: the playbook, the user's profile and the ranked list.

Usage: python scripts/render_guide.py profiles/ui-ux out/ranked.json out/guide.html [--open] [--demo]
--demo adds a banner saying the page uses sample data (used for the published demo).
--open launches the page in the default browser (Chrome, Safari, Edge...). On a machine with no
display, such as a cloud session, it only prints the file path; see SKILL.md for other ways to show it.
The page is static and local. Nothing is uploaded; it contains the user's own data, so
keep it out of public repos (out/ is git-ignored).
"""

import html
import json
import re
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from common import load_profile, tier_of


def md_to_html(md: str) -> str:
    """Tiny markdown subset: headings, bullets, numbered lists, bold, code, links, paragraphs."""
    out, in_list = [], None

    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)

    def close():
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>")
            in_list = None

    for line in md.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        b = re.match(r"^\s*[-*]\s+(.*)", line)
        n = re.match(r"^\s*\d+\.\s+(.*)", line)
        if m:
            close()
            level = len(m.group(1)) + 1
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
        elif b or n:
            kind = "ul" if b else "ol"
            if in_list != kind:
                close()
                out.append(f"<{kind}>")
                in_list = kind
            out.append(f"<li>{inline((b or n).group(1))}</li>")
        elif line.strip():
            close()
            out.append(f"<p>{inline(line)}</p>")
        else:
            close()
    close()
    return "\n".join(out)


DEMO_BANNER = (
    '<p class="note">Demo with <strong>sample data</strong>. '
    '<a href="https://github.com/lzcai-prod/job-search-skill">Get the skill</a> and ask your AI agent '
    "to run it on your own search.</p>"
)


def main(
    profile_dir: str, ranked_path: str, out_path: str, open_browser: bool = False, demo: bool = False
) -> None:
    profile = load_profile(profile_dir)
    ranked = json.loads(Path(ranked_path).read_text(encoding="utf-8"))
    chapters = sorted((ROOT / "playbook").glob("*.md"))
    playbook = "\n".join(md_to_html(c.read_text(encoding="utf-8")) for c in chapters)
    goal = profile.get("goal", {})
    places = ", ".join(goal.get("locations", [])) or "any location"
    summary = html.escape(f"{goal.get('summary', '')} ({goal.get('level', '')}; {places})")
    data = {
        "ranked": ranked,
        "companies": [
            {"company": c["company"], "bucket": c.get("bucket", ""), "tier": tier_of(profile, c["company"])}
            for c in profile["companies"]
        ],
        "profile": {"name": Path(profile_dir).name},
    }
    # keep "</script>" out of the embedded JSON
    blob = json.dumps(data).replace("</", "<\\/")
    page = (ROOT / "templates" / "guide.html").read_text(encoding="utf-8")
    page = (
        page.replace("{{PROFILE}}", summary)
        .replace("{{PLAYBOOK}}", playbook)
        .replace("{{BANNER}}", DEMO_BANNER if demo else "")
        .replace("{{DATA}}", blob)
    )
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
