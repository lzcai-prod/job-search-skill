import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_board
import find_boards
import rank
import render_guide
from common import load_profile, tier_of

PROFILE = ROOT / "profiles" / "ui-ux"
SAMPLE = ROOT / "examples" / "sample_postings.json"


def ranked():
    postings = json.loads(SAMPLE.read_text(encoding="utf-8"))
    return rank.rank(postings, load_profile(PROFILE))


def test_ranking_is_top_down_and_filters():
    out = ranked()
    titles = [r["title"] for r in out]
    assert "Senior Software Engineer" not in titles  # negative keywords
    assert "Senior Product Designer" not in titles  # excluded seniority
    assert "Sales Development Representative" not in titles
    assert titles[0] in {"Product Design Intern", "UX Researcher, Intern"}  # tier 1 first
    assert [r["tier"] for r in out] == sorted(r["tier"] for r in out)
    assert all(r["reasons"] for r in out)


def test_unknown_company_gets_default_tier():
    assert tier_of(load_profile(PROFILE), "Some Startup") == 5


def test_parsers_normalise_postings():
    gh = {"jobs": [{"title": "Designer", "location": {"name": "NYC"}, "absolute_url": "u", "content": "&lt;p&gt;Hi&lt;/p&gt;"}]}
    p = fetch_board.parse_greenhouse("Co", gh)[0]
    assert p["company"] == "Co" and p["description"] == "Hi" and p["ats"] == "greenhouse"
    lv = [{"text": "UX", "categories": {"location": "Remote"}, "hostedUrl": "u", "descriptionPlain": "d", "createdAt": 1}]
    assert fetch_board.parse_lever("Co", lv)[0]["location"] == "Remote"
    ab = {"jobs": [{"title": "T", "location": "L", "jobUrl": "u", "descriptionPlain": "d"}]}
    assert fetch_board.parse_ashby("Co", ab)[0]["title"] == "T"


def test_candidate_slugs():
    assert find_boards.candidate_slugs("Open AI Labs") == ["openailabs", "open-ai-labs"]


def test_render_guide(tmp_path):
    ranked_path = tmp_path / "ranked.json"
    ranked_path.write_text(json.dumps(ranked()), encoding="utf-8")
    out = tmp_path / "guide.html"
    render_guide.main(str(PROFILE), str(ranked_path), str(out))
    page = out.read_text(encoding="utf-8")
    assert "Product Design Intern" in page and "{{" not in page


def test_demo_banner(tmp_path):
    ranked_path = tmp_path / "ranked.json"
    ranked_path.write_text(json.dumps(ranked()), encoding="utf-8")
    out = tmp_path / "demo.html"
    render_guide.main(str(PROFILE), str(ranked_path), str(out), demo=True)
    page = out.read_text(encoding="utf-8")
    assert "sample data" in page and "{{" not in page
