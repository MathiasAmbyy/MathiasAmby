#!/usr/bin/env python3
"""
Seed sample movies and ratings into movie_tracker.db for testing.
Run: .venv\Scripts\python.exe seed_data.py
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'movie_tracker.db')
SAMPLE_MOVIES = [
    {'title':'The Matrix','director':'Wachowski','release_year':1999,'runtime':136,'genres':'Action,Sci-Fi','poster_path':''},
    {'title':'Inception','director':'Christopher Nolan','release_year':2010,'runtime':148,'genres':'Action,Sci-Fi','poster_path':''},
    {'title':'Parasite','director':'Bong Joon-ho','release_year':2019,'runtime':132,'genres':'Drama,Thriller','poster_path':''},
]
SAMPLE_RATINGS = [
    # movie_title, reviewer, rating
    ('The Matrix','Quentin BabyBino',9),
    ('The Matrix','Nars Von Larsen',8),
    ('The Matrix','Steven Spejlblank',10),
    ('Inception','Quentin BabyBino',8),
    ('Inception','Christopher Hoe-Man',9),
    ('Parasite','Nars Von Larsen',10),
    ('Parasite','Steven Spejlblank',9),
]

def ensure_db():
    if not os.path.exists(DB):
        print('Database does not exist. Run init_db.py first.')
        return False
    return True


def seed():
    if not ensure_db():
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # insert movies if missing
    movie_map = {}
    for m in SAMPLE_MOVIES:
        cur.execute('SELECT id FROM movies WHERE lower(title)=?', (m['title'].lower(),))
        r = cur.fetchone()
        if r:
            movie_map[m['title']] = r[0]
        else:
            cur.execute('INSERT INTO movies (title, director, release_year, runtime, genres, poster_path) VALUES (?,?,?,?,?,?)',
                        (m['title'], m['director'], m['release_year'], m['runtime'], m['genres'], m['poster_path']))
            movie_map[m['title']] = cur.lastrowid
    conn.commit()

    # insert ratings if not duplicate
    for title, reviewer, rating in SAMPLE_RATINGS:
        movie_id = movie_map.get(title)
        if not movie_id:
            continue
        cur.execute('SELECT id FROM ratings WHERE movie_id=? AND reviewer=? AND rating=?', (movie_id, reviewer, rating))
        if cur.fetchone():
            continue
        cur.execute('INSERT INTO ratings (movie_id, reviewer, rating) VALUES (?,?,?)', (movie_id, reviewer, rating))
    conn.commit()
    print('Seeded sample movies and ratings.')

if __name__ == '__main__':
    seed()
