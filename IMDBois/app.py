from flask import Flask, render_template, request, jsonify, g
import sqlite3
import os
import requests

DATABASE = os.path.join(os.path.dirname(__file__), 'movie_tracker.db')
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w185'
TMDB_API_KEY_FILE = os.path.join(os.path.dirname(__file__), '.tmdb_api_key')
FALLBACK_POSTER_PATH = '/static/poster-placeholder.svg'
REVIEWERS = [
    'Quentin BabyBino',
    'Nars Von Larsen',
    'Steven Spejlblank',
    'Christopher Hoe-Man'
]

app = Flask(__name__, 
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static'))

FALLBACK_MOVIES = [
    {
        'title': 'The Matrix',
        'tmdb_id': '603',
        'release_date': '1999-03-31',
        'overview': 'A computer hacker learns that reality is a simulation and joins a rebellion.',
        'poster_path': FALLBACK_POSTER_PATH,
    },
    {
        'title': 'Inception',
        'tmdb_id': '27205',
        'release_date': '2010-07-16',
        'overview': 'A thief who steals secrets from dreams is tasked with planting an idea.',
        'poster_path': FALLBACK_POSTER_PATH,
    },
    {
        'title': 'Parasite',
        'tmdb_id': '496243',
        'release_date': '2019-05-30',
        'overview': 'A poor family schemes to infiltrate a wealthy household.',
        'poster_path': FALLBACK_POSTER_PATH,
    },
]


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def get_tmdb_api_key():
    api_key = os.environ.get('TMDB_API_KEY', '').strip()
    if api_key:
        return api_key
    try:
        with open(TMDB_API_KEY_FILE, 'r', encoding='utf-8') as fh:
            return fh.read().strip()
    except FileNotFoundError:
        return ''


def resolve_poster_path(poster_path):
    if not poster_path:
        return FALLBACK_POSTER_PATH
    if poster_path.startswith('http://') or poster_path.startswith('https://'):
        return poster_path
    if poster_path.startswith('/'):
        return f"{TMDB_IMAGE_BASE}{poster_path}"
    return f"{TMDB_IMAGE_BASE}/{poster_path}"


def fallback_search(query):
    q = (query or '').strip().lower()
    if not q:
        return []
    matches = []
    for item in FALLBACK_MOVIES:
        title = item['title'].lower()
        if q in title:
            matches.append(dict(item))
    return matches[:10]


def tmdb_search(query):
    api_key = get_tmdb_api_key()
    if not api_key:
        return []
    url = 'https://api.themoviedb.org/3/search/movie'
    try:
        r = requests.get(url, params={'api_key': api_key, 'query': query, 'page': 1}, timeout=10)
        data = r.json()
        out = []
        for item in data.get('results', [])[:20]:
            poster = item.get('poster_path')
            out.append({
                'title': item.get('title'),
                'tmdb_id': item.get('id'),
                'release_date': item.get('release_date'),
                'overview': item.get('overview'),
                'poster_path': resolve_poster_path(poster)
            })
        return out
    except Exception:
        return []


def tmdb_get_details(tmdb_id):
    api_key = get_tmdb_api_key()
    if not api_key or not tmdb_id:
        return None
    url = f'https://api.themoviedb.org/3/movie/{tmdb_id}'
    try:
        r = requests.get(url, params={'api_key': api_key, 'append_to_response': 'credits'}, timeout=10)
        if r.status_code != 200:
            return None
        j = r.json()
        genres = [g['name'] for g in j.get('genres', [])]
        runtime = j.get('runtime')
        release_year = None
        if j.get('release_date'):
            try:
                release_year = int(j['release_date'][:4])
            except Exception:
                release_year = None
        director = None
        for c in j.get('credits', {}).get('crew', []):
            if c.get('job') == 'Director':
                director = c.get('name')
                break
        return {
            'tmdb_id': tmdb_id,
            'title': j.get('title'),
            'genres': ','.join(genres),
            'director': director,
            'release_year': release_year,
            'runtime': runtime,
            'overview': j.get('overview'),
            'poster_path': resolve_poster_path(j.get('poster_path'))
        }
    except Exception:
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/stats')
def stats_page():
    return render_template('stats.html', TMDB_IMAGE_BASE=TMDB_IMAGE_BASE)


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    if get_tmdb_api_key():
        results = tmdb_search(q)
        if results:
            return jsonify(results)

    db = get_db()
    cur = db.execute("SELECT id, title, tmdb_id, release_year, genres, director, overview, poster_path FROM movies WHERE lower(title) LIKE ? ORDER BY title LIMIT 20", (f"%{q.lower()}%",))
    rows = [dict(r) for r in cur.fetchall()]

    for m in rows:
        m['poster_path'] = resolve_poster_path(m.get('poster_path'))
        m['release_date'] = f"{m['release_year']}-01-01" if m.get('release_year') else None
        cur2 = db.execute('SELECT reviewer, rating FROM ratings WHERE movie_id=?', (m['id'],))
        revs = cur2.fetchall()
        rr = {}
        for r in revs:
            rr[r['reviewer']] = r['rating']
        m['reviewer_ratings'] = rr

    if rows:
        return jsonify(rows)

    fallback_results = fallback_search(q)
    return jsonify(fallback_results)


@app.route('/api/reviewers')
def reviewers():
    # Return the list of allowed reviewers
    return jsonify(REVIEWERS)


@app.route('/api/reviews')
def reviews():
    db = get_db()
    reviewer_filter = request.args.get('reviewer')
    if reviewer_filter:
        cur = db.execute('''
            SELECT r.id, r.movie_id, m.title as movie_title, r.reviewer, r.rating, r.created_at, m.release_year
            FROM ratings r
            JOIN movies m ON m.id = r.movie_id
            WHERE r.reviewer = ?
            ORDER BY r.created_at DESC
        ''', (reviewer_filter,))
    else:
        cur = db.execute('''
            SELECT r.id, r.movie_id, m.title as movie_title, r.reviewer, r.rating, r.created_at, m.release_year
            FROM ratings r
            JOIN movies m ON m.id = r.movie_id
            ORDER BY r.created_at DESC
        ''')
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)


@app.route('/api/rate', methods=['POST'])
def rate():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    tmdb_id = data.get('tmdb_id')
    try:
        rating = int(data.get('rating'))
    except Exception:
        return jsonify({'error': 'rating must be an integer 1-10'}), 400
    if not title or not (1 <= rating <= 10):
        return jsonify({'error': 'invalid title or rating'}), 400

    db = get_db()
    movie_id = None
    # Prefer matching by TMDB id if provided
    if tmdb_id:
        cur = db.execute('SELECT id FROM movies WHERE tmdb_id=?', (str(tmdb_id),))
        row = cur.fetchone()
        if row:
            movie_id = row['id']
        else:
            details = tmdb_get_details(tmdb_id)
            if details:
                cur = db.execute('INSERT INTO movies (title, tmdb_id, genres, director, release_year, runtime, overview, poster_path) VALUES (?,?,?,?,?,?,?,?)',
                                 (details['title'], str(details['tmdb_id']), details['genres'], details['director'], details['release_year'], details['runtime'], details['overview'], details['poster_path']))
                db.commit()
                movie_id = cur.lastrowid
    # Fallback: try to find by title
    if not movie_id:
        cur = db.execute('SELECT id FROM movies WHERE lower(title)=?', (title.lower(),))
        row = cur.fetchone()
        if row:
            movie_id = row['id']
        else:
            cur = db.execute('INSERT INTO movies (title) VALUES (?)', (title,))
            db.commit()
            movie_id = cur.lastrowid

    reviewer = (data.get('reviewer') or '').strip()
    if reviewer not in REVIEWERS:
        return jsonify({'error': 'invalid reviewer'}), 400
    db.execute('INSERT INTO ratings (movie_id, reviewer, rating) VALUES (?, ?, ?)', (movie_id, reviewer, rating))
    db.commit()

    cur = db.execute('SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM ratings WHERE movie_id=?', (movie_id,))
    stats = cur.fetchone()
    return jsonify({'id': movie_id, 'title': title, 'avg': round(stats['avg_rating'], 2), 'count': stats['count']})


@app.route('/api/stats')
def stats():
    db = get_db()
    reviewer_filter = request.args.get('reviewer')
    # Build base query; allow optional reviewer filter to inspect individual's stats
    if reviewer_filter:
        cur = db.execute('''
            SELECT m.id, m.title, m.genres, m.director, m.release_year, m.runtime, ROUND(AVG(r.rating),2) as avg_rating, COUNT(r.id) as count
            FROM movies m
            JOIN ratings r ON r.movie_id = m.id
            WHERE r.reviewer = ?
            GROUP BY m.id
            HAVING COUNT(r.id) > 0
            ORDER BY avg_rating DESC, count DESC
            LIMIT 100
        ''', (reviewer_filter,))
    else:
        cur = db.execute('''
            SELECT m.id, m.title, m.genres, m.director, m.release_year, m.runtime, ROUND(AVG(r.rating),2) as avg_rating, COUNT(r.id) as count
            FROM movies m
            JOIN ratings r ON r.movie_id = m.id
            GROUP BY m.id
            HAVING COUNT(r.id) > 0
            ORDER BY avg_rating DESC, count DESC
            LIMIT 100
        ''')
    rows = [dict(r) for r in cur.fetchall()]

    # Build aggregates
    genre_counts = {}
    director_counts = {}
    year_counts = {}
    total_runtime = 0
    runtime_count = 0
    for m in rows:
        if m.get('genres'):
            for g in (m['genres'] or '').split(','):
                g = g.strip()
                if not g: continue
                genre_counts[g] = genre_counts.get(g, 0) + 1
        if m.get('director'):
            d = m['director']
            director_counts[d] = director_counts.get(d, 0) + 1
        if m.get('release_year'):
            y = m['release_year']
            year_counts[y] = year_counts.get(y, 0) + 1
        if m.get('runtime'):
            try:
                total_runtime += int(m['runtime'])
                runtime_count += 1
            except Exception:
                pass

    avg_runtime = round(total_runtime / runtime_count, 1) if runtime_count else None

    reviewer_counts = {}
    if reviewer_filter:
        cur = db.execute('SELECT reviewer, COUNT(*) as count FROM ratings WHERE reviewer=? GROUP BY reviewer', (reviewer_filter,))
    else:
        cur = db.execute('SELECT reviewer, COUNT(*) as count FROM ratings GROUP BY reviewer ORDER BY count DESC')
    for row in cur.fetchall():
        reviewer_counts[row['reviewer']] = row['count']

    aggregates = {
        'top_genres': sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        'top_directors': sorted(director_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        'years': sorted(year_counts.items(), key=lambda x: x[0]),
        'avg_runtime': avg_runtime,
        'top_reviewers': sorted(reviewer_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    }

    return jsonify({'movies': rows, 'aggregates': aggregates})


if __name__ == '__main__':
    app.run(debug=True)
