# Added files and purpose

This file documents the additional scripts and files I added while working on stats and reviewer features.

- `static/stats.js` — Rewritten/extended to render the statistics page with: dynamic reviewer columns, per-movie reviewer rating cells, rating distribution chart. Contains debug logs when needed.
- `static/poster_placeholder.svg` — Simple SVG placeholder used for posters when none are available.
- `static/styles.css` (edited) — Added styling rules for reviewer filter, chart canvas, and optional thumbnails.
- `app.py` (edited) — Backend updates:
  - `/api/reviewers` endpoint returns fixed reviewers list
  - `/api/reviews` endpoint returns individual review records (supports `?reviewer=` filter)
  - `/api/stats` now includes `reviewer_ratings` per movie
  - passes `TMDB_IMAGE_BASE` to templates
- `seed_data.py` — Script to insert sample movies and ratings for testing; run with `.venv\Scripts\python.exe seed_data.py`.
- `seeded sample data` — I ran `seed_data.py` locally to populate some example rows.
- `seed_data.py` and `tools/inspect_stats.py` — utilities for seeding and inspecting database content.
- `tools/create_isolated_copy.py` — Script to copy the entire project into `./isolated_project` (excludes `.git`, `isolated_project`, virtualenv folders). Run with `.venv\Scripts\python.exe tools\create_isolated_copy.py`.
- `reset_db.py` — Script to delete all rows from `ratings` and `movies` and `VACUUM` the database. Run with `.venv\Scripts\python.exe reset_db.py`.

Context / how to use

- To start fresh (clear DB):

```bash
.venv\Scripts\python.exe reset_db.py
```

- To seed example data (after reset):

```bash
.venv\Scripts\python.exe seed_data.py
```

- To create an isolated copy of the project in `isolated_project`:

```bash
.venv\Scripts\python.exe tools\create_isolated_copy.py
```

Notes

- I ran `reset_db.py` and re-seeded sample data during development; if you want me to leave the DB empty instead, I can revert that and keep it cleared.
- `static/stats.js` contains temporary debug console.logs; I can remove them when you're satisfied.
