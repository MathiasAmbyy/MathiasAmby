#!/usr/bin/env python3
"""
Reset the SQLite database by deleting all rows from `ratings` and `movies`.
Use with caution — this irreversibly removes data.
Run:
.venv\Scripts\python.exe reset_db.py
"""
import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'movie_tracker.db')
if not os.path.exists(DB):
    print('Database not found at', DB)
    raise SystemExit(1)
conn = sqlite3.connect(DB)
cur = conn.cursor()
print('Deleting rows from ratings and movies...')
cur.execute('DELETE FROM ratings')
cur.execute('DELETE FROM movies')
conn.commit()
print('Vacuuming database...')
cur.execute('VACUUM')
conn.close()
print('Database reset complete.')
