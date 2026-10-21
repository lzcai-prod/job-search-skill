# Building keywords, buckets and tiers

**Files in a profile folder**
- `profile.toml`: goal, level, locations, excluded title words, bucket ranking.
- `keywords.toml`: `[positive]` and `[negative]` term-to-weight tables, `title_multiplier`, `min_score`.
- `companies.csv`: `company, bucket, tier, ats, slug, notes`.

**Keywords**
- Positive: exact role titles (weight 3 to 4), adjacent titles (2 to 3), useful skills and tools (1).
- Negative: titles that look similar but are not the role (weight 3 to 4).
- Put seniority words you are too junior for in `exclude_titles`, not in negative keywords.
- Start loose, look at the top 20 results and the near-misses, then adjust. Raise `min_score` if there is too much noise.

**Tiers**: 1 is best. Score each company 1 to 5 on team quality, junior hiring, location, pay and interest, then weight by what the user cares about. Always get the user to confirm the top tier.

**Check** by running `python scripts/rank.py profiles/<name> examples/sample_postings.json out/ranked.json` and reading the `reasons`.
