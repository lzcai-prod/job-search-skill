"""Keyword scoring of one posting against a profile.

Title matches count `title_multiplier` times; description matches count once.
Negative keywords subtract. Seniority and location checks are filters, not scores.
Returns (score, reasons) so the ranked list can show why a posting scored as it did.
"""


def _hits(text: str, terms: dict[str, float]) -> list[tuple[str, float]]:
    low = text.lower()
    return [(t, w) for t, w in terms.items() if t.lower() in low]


def score_posting(posting: dict, profile: dict) -> tuple[float, list[str]]:
    kw = profile["keywords"]
    mult = float(kw.get("title_multiplier", 3))
    title, desc = posting.get("title", ""), posting.get("description", "")
    total, reasons = 0.0, []
    for term, w in _hits(title, kw.get("positive", {})):
        total += w * mult
        reasons.append(f"+{w * mult:g} title: {term}")
    for term, w in _hits(desc, kw.get("positive", {})):
        total += w
        reasons.append(f"+{w:g} description: {term}")
    for term, w in _hits(title, kw.get("negative", {})):
        total -= abs(w) * mult
        reasons.append(f"-{abs(w) * mult:g} title: {term}")
    for term, w in _hits(desc, kw.get("negative", {})):
        total -= abs(w)
        reasons.append(f"-{abs(w):g} description: {term}")
    return total, reasons


def passes_filters(posting: dict, profile: dict) -> bool:
    """Location and seniority filters from profile.toml; empty lists mean no filter."""
    goal = profile.get("goal", {})
    title = posting.get("title", "").lower()
    if any(s.lower() in title for s in goal.get("exclude_titles", [])):
        return False
    places = [p.lower() for p in goal.get("locations", [])]
    loc = posting.get("location", "").lower()
    return not (places and loc and not any(p in loc for p in places))
