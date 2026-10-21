# When to outgrow the page's own storage

The tracker keeps application records in the page's private database (as a Claude artifact) or in the browser. That is enough for roughly a few hundred applications and one person. Move to a real database only when you hit one of these:

| Symptom | What it means |
|---|---|
| You track thousands of postings, not just applications | Document stores slow down; a SQL table does not |
| Several tools write the same records (a scanner, a mailbox scan, a dashboard) | You need one source of truth and an audit trail |
| You want charts and views that join postings, applications and contacts | SQL views are easier than page code |
| Two copies of the numbers disagree | Reconcile them in one place (see below) |

## Option: a hosted Postgres (for example Neon)
Optional, requires an account, and may cost money; do not set it up without the user's say-so.
- Use `schema.sql` as the starting point; add a `scan_log` table (`firm, scanned_at, ok, postings_found`) so you can see which boards were checked and when ("job health").
- Make `event` append-only and write a row on every status change.
- Add read-only **views** for the dashboard (funnel by status, applications per company, what to submit next, postings by tier). The page should only run fixed, read-only queries.
- Never let a connection string reach a published page.
- Keep **one** writer per record type. Two writers for the same data (for example a mailbox scan and manual edits) need an explicit rule for which wins.

## Reconciling two sources
If an older store and the new database overlap, compare them by normalised company name and report: counts on each side, rows only on one side, and rows where the status differs. Fix the data, then retire the old source. Do not keep both live.

## Order of work
1. Create the schema on a throw-away branch or database and load a copy of the data.
2. Check row counts against the old store.
3. Build the views and read them from the page.
4. Switch the page over; keep the old version available to roll back.
