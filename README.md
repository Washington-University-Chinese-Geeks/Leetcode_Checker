# Leetcode Dashboard

A static LeetCode progress dashboard for WUCG. This project has been
migrated from a Django / Celery / PostgreSQL deployment to a purely
frontend architecture that needs no backend servers to run.

## Architecture

```text
Google Sheets (member roster)
        │
        ▼
GitHub Actions  ──►  scripts/collect.py  ──►  data/*.json  (committed)
  (daily cron)                                    │
                                                  ▼
                                         Next.js static export
                                                  │
                                                  ▼
                                          GitHub Pages site
```

| Concern            | Where it lives                                     |
| ------------------ | -------------------------------------------------- |
| Scheduler          | `.github/workflows/collect.yml` (daily cron)       |
| Collector          | `scripts/collect.py` + `scripts/leetcode_api.py`   |
| Persistent storage | `data/` directory in this repo (JSON, git-tracked) |
| Schema validation  | `scripts/validator.py` + `scripts/schemas/*.json`  |
| Frontend           | `web/` (Next.js 14 App Router, static export)      |
| Hosting            | GitHub Pages (`.github/workflows/deploy.yml`)      |

There is no database, no long-running process, and no server to operate.
The repository itself is the source of truth — each collector run commits
a new snapshot of `data/`, and that push triggers a Pages redeploy.

## Repository layout

```text
.
├── .github/workflows/
│   ├── collect.yml         # daily cron → runs collector → commits data
│   └── deploy.yml          # builds web/ and publishes to GitHub Pages
├── scripts/
│   ├── collect.py          # orchestrator invoked by the cron workflow
│   ├── leetcode_api.py     # LeetCode GraphQL client (US + CN)
│   ├── google_sheet.py     # Google Sheets v4 roster reader
│   ├── validator.py        # JSON Schema validator for data/ artifacts
│   ├── parse_problems.py   # legacy text→CSV helper
│   ├── requirements.txt    # requests + jsonschema
│   └── schemas/
│       ├── user.schema.json
│       ├── submission.schema.json
│       └── summary.schema.json
├── data/
│   ├── summary.json        # top-level roster snapshot
│   └── users/<slug>.json   # per-member records (recent AC, totals, profile)
├── web/                    # Next.js frontend
│   ├── app/                # App Router pages (roster + per-user)
│   ├── lib/                # data loaders + shared types
│   ├── next.config.mjs     # static export + Pages base-path
│   └── package.json
├── AGENTS.md               # conventions for coding agents / contributors
└── README.md               # (this file)
```

The original Django / Celery source trees (`check/`, `member/`, `main/`,
`static/`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`,
`manage.py`, `entrypoint.sh`, `nginx/`) are kept in place for reference.
They are not used by the new pipeline and can be removed once the
migration has been verified in production.

## How a day looks

1. **07:15 UTC** — `collect.yml` cron fires.
2. `scripts/collect.py` reads the roster from Google Sheets, then calls
   the LeetCode GraphQL API once per unique `leetcode_username`.
3. Responses are normalized into the schemas in `scripts/schemas/` and
   written to `data/users/<slug>.json` + `data/summary.json`.
4. `scripts/validator.py` re-validates everything. If any file fails, the
   job exits non-zero and no commit happens.
5. If `data/` has changed, the workflow commits the diff with
   `chore(data): daily collector refresh YYYY-MM-DD` and pushes to `main`.
6. That push triggers `deploy.yml`, which runs `npm run build` in `web/`
   and uploads `web/out/` to GitHub Pages.

## Required repository secrets

Set these under **Settings → Secrets and variables → Actions**:

| Secret             | Purpose                                                |
| ------------------ | ------------------------------------------------------ |
| `GOOGLE_SHEET_ID`  | Spreadsheet id of the member roster.                   |
| `GOOGLE_API_KEY`   | API key with Google Sheets read access.                |

Enable GitHub Pages under **Settings → Pages**, selecting **GitHub
Actions** as the source.

## Roster sheet schema

The collector reads columns `A:Z` from the first worksheet, skipping the
header row. Columns (0-indexed):

| Col | Field                 | Notes                                |
| --- | --------------------- | ------------------------------------ |
|  0  | register_date         | `MM/DD/YYYY HH:MM:SS`                |
|  1  | leetcode_username     | **required**                         |
|  2  | server_region         | contains "cn" → CN, else US          |
|  3  | problems_per_week     | integer, blank for free-form         |
|  4  | start_date            | `YYYY-MM-DD`                         |
|  5  | expire_date           | `YYYY-MM-DD`, blank for no expiry    |
|  6  | scheduled_problems    | whitespace-separated problem codes   |
|  7  | email                 | identity key                         |
|  8  | mode                  | e.g. `Normal`, `Free`                |
|  9  | display_name          | optional, falls back to username     |

## Local development

### Collector

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r scripts/requirements.txt

export GOOGLE_SHEET_ID=...
export GOOGLE_API_KEY=...
python scripts/collect.py --dry-run     # fetch + validate, no writes
python scripts/collect.py               # write to data/
python scripts/validator.py             # re-validate everything
```

### Frontend

```bash
cd web
npm install
npm run dev                             # http://localhost:3000
npm run build                           # static export to web/out/
```

`web/lib/data.ts` reads from `../data` at build time. A brand-new clone
with an empty `data/` will still build — the roster page just renders an
empty state until the collector has run once.

## License

See [LICENSE](LICENSE).
