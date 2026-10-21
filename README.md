# job-search-skill

A method and a few small scripts for a **top-down, safe job search** that your own AI agent can run and explain to you. It ships with a UI/UX starter profile and a blank template for any other role.

**Top-down** means: pick the employers first, watch their public job boards, rank what appears, and review and submit every application yourself. The tool never submits for you.

**[See the live demo](https://lzcai-prod.github.io/job-search-skill/)** (sample data).

## Try it in 30 seconds (no setup, no network)
```
python scripts/rank.py profiles/ui-ux examples/sample_postings.json out/ranked.json
python scripts/render_guide.py profiles/ui-ux out/ranked.json out/guide.html
```
Open `out/guide.html` to see the ranked list, an application tracker, your employer list and the method in one page.

## Use it with an AI agent
Give your agent this folder (for example drop it in its skills directory) and say: *"Help me find UI/UX internships in New York using the job-search skill."* The agent reads `SKILL.md`, interviews you, builds your profile, fetches public job boards, ranks the results with reasons, and shows you a guide page. Any agent that reads `AGENTS.md` can follow the same steps.

## What is inside
| Path | Purpose |
|---|---|
| `SKILL.md` | The skill: workflow and hard rules for the agent |
| `playbook/` | The method in plain language, for you |
| `references/` | Details the agent loads when needed: sources, board endpoints, scoring, safety, data model, mailbox-scan recipe, scaling up |
| `profiles/` | `_template` (blank), `ui-ux` (starter) |
| `scripts/` | Detect boards, fetch postings, score, rank, render the guide (standard library only) |
| `examples/` | Fake postings so a fresh clone works immediately |
| `docs/` | The demo page, rebuilt from the sample data (served by GitHub Pages) |

## Track your applications
The guide has a **Tracker** tab: pressing Apply on a ranked posting adds it as "To apply", and you move it along a status ladder (Submitted, OA invited, Interview, Offer, Rejected...). Each change is kept in a history. Published as a Claude artifact it saves to the page's private database; anywhere else it saves in your browser, and **Export CSV** keeps a copy. Statuses and fields are in `references/data-model.md`. Optional extras: a read-only mailbox-scan recipe and a guide to outgrowing the page's storage.

## Make your own profile
Copy `profiles/_template` to `profiles/<your-search>/`, or ask your agent to interview you and fill it in. Profiles you create are git-ignored by default so your details stay local.

## Safety
- It never submits applications, never fills work-authorization or EEO fields, and never bypasses CAPTCHAs or log-ins.
- It uses only public job-board endpoints at one request per second, and you are responsible for following each site's terms.
- You are responsible for everything you submit.

## Develop
`pip install -e ".[dev]"`, then `pytest` and `ruff check .`. Contributions welcome; see `CONTRIBUTING.md`.

Licensed under MIT.
