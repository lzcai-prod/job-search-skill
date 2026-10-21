# Instructions for coding agents

This repository is a **skill**: a method (`playbook/`, `SKILL.md`) plus small scripts. Read `SKILL.md` first.

## Hard rules
- Never submit applications or fill work-authorization, sponsorship, EEO, disability or criminal-history fields.
- Never solve or bypass CAPTCHAs, rate limits or log-in walls.
- Never commit secrets or personal data (profiles, resumes, application logs, `.env`).
- No network access in tests; use `examples/` and small inline fixtures in the tests.

## Where things go
- A new search: copy `profiles/_template/` to `profiles/<name>/`. Do not edit `_template`.
- A new job board: add a parser and URL in `scripts/fetch_board.py`, a probe in `scripts/find_boards.py`, and a test.
- Method changes: edit the matching `playbook/` chapter. Keep the human text and `SKILL.md` consistent.

## Checks before finishing
`pip install -e ".[dev]"`, then `pytest` and `ruff check .`. Scripts use only the standard library (Python 3.11+).

## Style
Match surrounding code. Short functions, type hints, no speculative abstractions.
