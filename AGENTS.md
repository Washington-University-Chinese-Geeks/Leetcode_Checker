# AGENTS.md

Guidance for coding agents and contributors working on this repository.
Read this before making changes — it encodes architectural invariants
that are not obvious from any single file.

## 1. Shape of the project

This repository is a **serverless, git-persisted LeetCode dashboard**.
There are three moving parts; keep them independent and don't
cross-wire them:

1. **`scripts/`** — Python 3.11 data collectors. Pure standard library
   plus `requests` and `jsonschema`. No Django, no framework code, no
   package layout — each module is importable as a flat file.
2. **`data/`** — JSON snapshots committed to `main`. This is the only
   storage tier. Treat it as append-mostly but byte-stable: collector
   output must be deterministic when upstream data is unchanged.
3. **`web/`** — Next.js 14 App Router app, built with `output: 'export'`
   for GitHub Pages. Reads `data/` at build time only; never fetches at
   runtime.

The three directories communicate only through file contracts:

```text
Google Sheets → scripts/ → data/*.json → web/ → GitHub Pages
```

`scripts/` must not import from `web/`. `web/` must not import from
`scripts/`. Both must agree on the shapes in `scripts/schemas/*.json`.

## 2. Invariants you must preserve

- **No servers.** No Django, no Flask, no long-lived processes, no
  databases. If a change would require `manage.py`, something is wrong.
- **No runtime secrets in the browser.** Secrets live in GitHub Actions.
  The Next.js build runs in CI with no network access to LeetCode or
  Google Sheets — it only reads committed JSON.
- **Deterministic JSON.** `scripts/collect.py` writes with
  `json.dumps(..., sort_keys=True, indent=2)` plus a trailing newline so
  unchanged runs produce a zero-diff commit (the workflow skips commit
  on no diff). Any new writer must preserve this.
- **Schema-validated writes.** Every file under `data/` must validate
  against a schema in `scripts/schemas/`. Add new fields to the schema
  first, then to the writer, then to the frontend.
- **Per-user filename slugging.** Use the `slugify()` helper in
  `scripts/collect.py`. The Next.js `generateStaticParams()` in
  `web/app/users/[username]/page.tsx` assumes filenames match slugged
  usernames exactly.

## 3. Conventions per surface

### Python (`scripts/`)
- Target Python 3.11. Use `from __future__ import annotations` and PEP
  604 unions (`str | None`) — these are fine on 3.11.
- Keep modules flat and importable by path (`python scripts/collect.py`
  must work without `PYTHONPATH` tricks). `collect.py` imports siblings
  by bare name; don't turn `scripts/` into a package.
- Logging over `print`, except in `__main__` blocks that exist for
  ad-hoc debugging.
- Network calls go through `requests` with a timeout. Never leave a
  request un-timed.

### TypeScript (`web/`)
- Strict mode is on. New code must type-check under `npm run
  typecheck`.
- Types in `web/lib/types.ts` mirror the JSON schemas. When a schema
  changes, update types in the same PR.
- Server Components by default. Only add `"use client"` when you need
  interactivity — the whole site is a static export, so most pages
  should have zero client JS.
- Never import `node:fs` from a Client Component. Data loading goes
  through `web/lib/data.ts`, which is server-only.
- Links use `next/link` with trailing slashes (the export is configured
  with `trailingSlash: true`).

### GitHub Actions (`.github/workflows/`)
- `collect.yml` is the only workflow allowed to push to `main`. Its
  commits use the bot identity `leetcode-dashboard-bot` so humans can
  filter them.
- `deploy.yml` is read-only on the repo; it needs `pages: write` and
  `id-token: write` for the Pages deployment.
- Keep the Python and Node toolchain versions pinned
  (`python-version: "3.11"`, `node-version: "20"`). Bump deliberately.

## 4. Making common changes

### "I want to expose a new LeetCode field in the UI"

1. Extend `scripts/leetcode_api.py` to query it.
2. Add the field to `scripts/schemas/user.schema.json` (and
   `submission.schema.json` if it lives on a submission).
3. Update `build_user_record()` in `scripts/collect.py` to write it.
4. Mirror the new field in `web/lib/types.ts`.
5. Render it in the relevant page under `web/app/`.
6. Run `python scripts/collect.py --dry-run` then `python
   scripts/validator.py` to confirm schema + writer agree.

### "I want to change what the daily job does"

Edit `scripts/collect.py`. The workflow in `.github/workflows/collect.yml`
only wraps it — keep orchestration logic in Python, not YAML. If you
need a second scheduled task, add a new workflow rather than another
cron entry in the same file.

### "I want to support a new roster source"

Add a client beside `scripts/google_sheet.py` that returns the same
`Member` dataclass. `collect.py` should stay source-agnostic.

## 5. What to leave alone

Everything under `backup/` is **retired Django code** (the old `check/`,
`member/`, `main/`, `static/`, `nginx/`, `logs/` apps plus `manage.py`,
`Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `env.sample`, and
the old root `requirements.txt`). It is archived for historical
reference only and is not part of the current pipeline. Do not add
features to it, do not import from it, and do not resurrect it unless
the user explicitly asks.

## 6. Branching

Work happens directly on `main`. The `json-backend` migration branch
was merged into `main` on 2026-04-13; new work should branch from
`main` (or commit to it directly for small changes) rather than
resurrecting `json-backend`.

## 7. Quick sanity checks

Before opening a PR:

```bash
# Python side
python scripts/collect.py --dry-run
python scripts/validator.py

# Frontend side
cd web
npm run typecheck
npm run lint
npm run build
```

A green run of all five is the minimum bar.
