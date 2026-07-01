import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'movie_tracker.db')


def init():
  need_init = not os.path.exists(DB)
  conn = sqlite3.connect(DB)
  cur = conn.cursor()

  # Create tables if they don't exist
  cur.executescript('''
  CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    tmdb_id TEXT,
    genres TEXT,
    director TEXT,
    release_year INTEGER,
    runtime INTEGER,
    overview TEXT,
    poster_path TEXT
  );
  CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movie_id INTEGER NOT NULL,
    reviewer TEXT NOT NULL,
    rating INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(movie_id) REFERENCES movies(id)
  );
  ''')

  # If DB existed but columns might be missing (migrations), add any missing columns
  cur.execute("PRAGMA table_info(movies)")
  cols = [r[1] for r in cur.fetchall()]
  extras = {
    'tmdb_id': 'TEXT',
    'genres': 'TEXT',
    'director': 'TEXT',
    'release_year': 'INTEGER',
    'runtime': 'INTEGER',
    'overview': 'TEXT',
    'poster_path': 'TEXT'
  }
  cur.execute("PRAGMA table_info(ratings)")
  rating_cols = [r[1] for r in cur.fetchall()]
  if 'reviewer' not in rating_cols:
    try:
      cur.execute('ALTER TABLE ratings ADD COLUMN reviewer TEXT')
    except Exception:
      pass
  for name, coltype in extras.items():
    if name not in cols:
      try:
        cur.execute(f'ALTER TABLE movies ADD COLUMN {name} {coltype}')
      except Exception:
        pass

  conn.commit()
  conn.close()
  if need_init:
    print('Initialized DB at', DB)
  else:
    print('DB exists at', DB, '- ensured schema updated')


if __name__ == '__main__':
  init()
