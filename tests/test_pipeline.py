import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import fetch_board
import find_boards
import rank
import render_guide
from common import MAX_RESPONSE_BYTES, STATUSES, load_profile, tier_of, valid_slug

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


def test_valid_slug_accepts_board_slugs_only():
    assert all(valid_slug(s) for s in ["figma", "open-ai", "acme.co", "a_b", "x" * 64])
    for bad in ["", "../x", "a/b", "a?b=1", "a#b", "a b", "-x", "x" * 65, "a@b"]:
        assert not valid_slug(bad)


def test_candidate_slugs_drop_invalid_hint():
    assert find_boards.candidate_slugs("Acme", hint="../etc") == ["acme"]


def test_fetch_skips_invalid_slug(tmp_path, monkeypatch):
    prof = tmp_path / "p"
    prof.mkdir()
    for name in ("profile.toml", "keywords.toml"):
        (prof / name).write_text("", encoding="utf-8")
    (prof / "companies.csv").write_text("company,ats,slug\nEvil,greenhouse,../x\n", encoding="utf-8")
    monkeypatch.setattr(fetch_board, "fetch", lambda *a: (_ for _ in ()).throw(AssertionError("fetched")))
    out = tmp_path / "out.json"
    fetch_board.main(str(prof), str(out))
    assert json.loads(out.read_text(encoding="utf-8")) == []


def test_get_json_rejects_oversized_response(monkeypatch):
    class Resp:
        def __init__(self, data):
            self.data = data

        def read(self, n=-1):
            return self.data[:n] if n >= 0 else self.data

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(fetch_board.time, "sleep", lambda s: None)
    monkeypatch.setattr(fetch_board.urllib.request, "urlopen", lambda *a, **k: Resp(b"[" + b"1," * MAX_RESPONSE_BYTES + b"1]"))
    try:
        fetch_board.get_json("https://example.com/x")
    except ValueError as exc:
        assert "too large" in str(exc)
    else:
        raise AssertionError("oversized response accepted")
    monkeypatch.setattr(fetch_board.urllib.request, "urlopen", lambda *a, **k: Resp(b'{"jobs": []}'))
    assert fetch_board.get_json("https://example.com/x") == {"jobs": []}
