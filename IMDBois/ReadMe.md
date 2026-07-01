# IMDBois - Movie Tracker

Simple Flask + SQLite app to track movies and ratings among friends. The project code is located in the `IMDBois/` folder.

## Quick start

Navigate to the `IMDBois/` folder:

```bash
cd IMDBois
```

1. Create a virtualenv and install deps:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Set your TMDB API key for richer movie search and metadata:

```powershell
$env:TMDB_API_KEY="your_tmdb_api_key"
```

3. Initialize database and run the app:

```bash
python init_db.py
python app.py
```

Open http://127.0.0.1:5000

Når appen kører, kan du besøge:
- http://127.0.0.1:5000 for søgesiden
- http://127.0.0.1:5000/stats for statistikoversigten

## Features

- Search movies via TMDB or local database
- Rate movies individually by reviewer (Quentin BabyBino, Nars Von Larsen, Steven Spejlblank, Christopher Hoe-Man)
- View statistics page with top genres, directors, reviewers, release years, and average runtime
- Visualize rating distribution with a bar chart
- Filter statistics by reviewer
- Purple-themed responsive UI in Danish

If `TMDB_API_KEY` is set, the app will search TMDB and store movie metadata like genre, director, release year, runtime, overview, and poster path.