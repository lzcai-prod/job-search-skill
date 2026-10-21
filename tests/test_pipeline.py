import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_board
import find_boards
import rank
import render_guide
from common import STATUSES, load_profile, tier_of

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


def embedded(path):
    page = path.read_text(encoding="utf-8")
    return json.loads(page.split('id="data">', 1)[1].split("</script>", 1)[0])


def render(tmp_path, demo):
    ranked_path = tmp_path / "ranked.json"
    ranked_path.write_text(json.dumps(ranked()), encoding="utf-8")
    out = tmp_path / ("demo.html" if demo else "real.html")
    render_guide.main(str(PROFILE), str(ranked_path), str(out), demo=demo)
    return out


def test_render_guide_real_has_no_sample_rows(tmp_path):
    data = embedded(render(tmp_path, demo=False))
    assert data["demo"] is False and data["seedApps"] == [] and data["jds"] == []
    assert data["statuses"] == STATUSES
    assert data["families"][0]["name"] == "product design"
    assert data["buckets"][0] == "design_forward_product"


def test_render_guide_demo_has_sample_rows(tmp_path):
    out = render(tmp_path, demo=True)
    page = out.read_text(encoding="utf-8")
    data = embedded(out)
    assert "sample data" in page and "{{" not in page
    assert len(data["seedApps"]) == 5 and len(data["jds"]) == 2


def test_data_model_lists_every_status():
    text = (ROOT / "references" / "data-model.md").read_text(encoding="utf-8")
    assert all(f"| {s['name']} |" in text for s in STATUSES)


def test_sample_applications_use_known_statuses_and_universe_firms():
    names = {s["name"] for s in STATUSES}
    seed = json.loads((ROOT / "examples" / "sample_applications.json").read_text(encoding="utf-8"))
    firms = {c["company"] for c in load_profile(PROFILE)["companies"]}
    assert all(a["status"] in names and a["company"] in firms for a in seed)
