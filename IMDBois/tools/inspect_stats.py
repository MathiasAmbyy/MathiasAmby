import sqlite3, json, os
DB = os.path.join(os.path.dirname(__file__), '..', 'movie_tracker.db')
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.execute('''
    SELECT m.id, m.title, m.genres, m.director, m.release_year, m.runtime, ROUND(AVG(r.rating),2) as avg_rating, COUNT(r.id) as count
    FROM movies m
    JOIN ratings r ON r.movie_id = m.id
    GROUP BY m.id
    HAVING COUNT(r.id) > 0
    ORDER BY avg_rating DESC, count DESC
    LIMIT 100
''')
rows = [dict(r) for r in cur.fetchall()]
for m in rows:
    cur2 = conn.execute('SELECT reviewer, rating FROM ratings WHERE movie_id=?', (m['id'],))
    rr = {}
    for r in cur2.fetchall():
        rr[r['reviewer']] = r['rating']
    m['reviewer_ratings'] = rr
print(json.dumps({'movies': rows}, indent=2, ensure_ascii=False))
