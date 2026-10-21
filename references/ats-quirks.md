# Public job-board endpoints

| ATS | Endpoint | Notes |
|---|---|---|
| Greenhouse | `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true` | `content=true` includes the description (HTML-escaped). |
| Lever | `https://api.lever.co/v0/postings/{slug}?mode=json` | Returns a list; `createdAt` is epoch milliseconds. |
| Ashby | `https://api.ashbyhq.com/posting-api/job-board/{slug}` | Returns `{"jobs": [...]}`. |

- A slug is usually the lowercase company name, sometimes with a hyphen or a suffix. `find_boards.py` probes guesses; always review them.
- Some companies use Workday or a custom careers page. Those need a rendered-page scanner, which this skill does not include. Add them by hand or paste the listings.
- Boards change and endpoints can disappear. Treat an empty result as "check by hand", not "no jobs".
- Postings can be duplicated across locations. De-duplicate by URL.
