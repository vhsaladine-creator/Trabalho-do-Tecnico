from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import os

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'sportzone.db'

app = Flask(__name__)
app.secret_key = os.getenv('SPORTZONE_SECRET', 'dev-secret-change-me')

ARCADE_GAMES = [
    {'key': 'Tiger Dash', 'slug': 'tiger', 'icon': '🐯', 'tag': 'REFLEXO', 'title': 'Tiger Dash', 'desc': 'Acerte o tigre em movimento durante 10 segundos.', 'limit': 50},
    {'key': 'Snake Trail', 'slug': 'snake', 'icon': '🐍', 'tag': 'MEMÓRIA', 'title': 'Snake Trail', 'desc': 'Repita sequências e avance até o nível 10.', 'limit': 100},
    {'key': 'Dragon Match', 'slug': 'dragon', 'icon': '🐉', 'tag': 'PARES', 'title': 'Dragon Match', 'desc': 'Encontre todos os pares de símbolos no tabuleiro.', 'limit': 24},
    {'key': 'Lantern Memory', 'slug': 'lantern', 'icon': '🏮', 'tag': 'MEMÓRIA', 'title': 'Lantern Memory', 'desc': 'Memorize onde as lanternas apareceram e marque as casas certas.', 'limit': 16},
    {'key': 'Panda Tap', 'slug': 'panda', 'icon': '🐼', 'tag': 'RITMO', 'title': 'Panda Tap', 'desc': 'Clique somente quando o panda aparecer e evite os falsos sinais.', 'limit': 30},
    {'key': 'Jade Steps', 'slug': 'jade', 'icon': '🀄', 'tag': 'SEQUÊNCIA', 'title': 'Jade Steps', 'desc': 'Siga a trilha numérica antes que o cronômetro termine.', 'limit': 20},
]


def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db_conn()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        score INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sport TEXT NOT NULL,
        league TEXT NOT NULL,
        home TEXT NOT NULL,
        away TEXT NOT NULL,
        starts_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'upcoming',
        score_home INTEGER,
        score_away INTEGER
    );

    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        match_id INTEGER NOT NULL,
        pick TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        points_awarded INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, match_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(match_id) REFERENCES matches(id)
    );

    CREATE TABLE IF NOT EXISTS arcade_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game TEXT NOT NULL,
        score INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    ''')

    if conn.execute('SELECT COUNT(*) AS n FROM matches').fetchone()['n'] == 0:
        now = datetime.now()
        rows = [
            ('Futebol', 'Brasileirão', 'Palmeiras', 'Flamengo', now + timedelta(minutes=18), 'live', 1, 1),
            ('Futebol', 'Brasileirão', 'São Paulo', 'Corinthians', now + timedelta(hours=3), 'upcoming', None, None),
            ('Futebol', 'Champions League', 'Real Madrid', 'Manchester City', now + timedelta(days=1, hours=1), 'upcoming', None, None),
            ('Basquete', 'NBA', 'Lakers', 'Celtics', now + timedelta(hours=6), 'upcoming', None, None),
            ('Tênis', 'ATP', 'Carlos Alcaraz', 'Jannik Sinner', now + timedelta(days=1, hours=2), 'upcoming', None, None),
            ('Futebol', 'Premier League', 'Arsenal', 'Liverpool', now + timedelta(days=2), 'upcoming', None, None),
            ('Basquete', 'NBB', 'Franca', 'Minas', now + timedelta(days=1, hours=5), 'upcoming', None, None),
            ('Futebol', 'La Liga', 'Barcelona', 'Atlético de Madrid', now + timedelta(days=3), 'upcoming', None, None),
            ('Tênis', 'WTA', 'Iga Swiatek', 'Coco Gauff', now + timedelta(days=2, hours=4), 'upcoming', None, None),
        ]
        conn.executemany('''
            INSERT INTO matches(sport, league, home, away, starts_at, status, score_home, score_away)
            VALUES(?,?,?,?,?,?,?,?)
        ''', [(r[0], r[1], r[2], r[3], r[4].isoformat(timespec='minutes'), r[5], r[6], r[7]) for r in rows])

    if not conn.execute('SELECT id FROM users WHERE email=?', ('demo@sportzone.local',)).fetchone():
        conn.execute(
            'INSERT INTO users(name,email,password_hash,score) VALUES(?,?,?,?)',
            ('Visitante Demo', 'demo@sportzone.local', generate_password_hash('demo123'), 1250)
        )

    conn.commit()
    conn.close()


def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    conn = db_conn()
    user = conn.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
    conn.close()
    return user


@app.context_processor
def inject_globals():
    return {'current_user': current_user(), 'arcade_games': ARCADE_GAMES}


@app.route('/')
def home():
    sport = request.args.get('sport', 'Todos')
    if sport not in {'Todos', 'Futebol', 'Basquete', 'Tênis'}:
        sport = 'Todos'

    conn = db_conn()
    if sport == 'Todos':
        matches = conn.execute('''
            SELECT * FROM matches
            ORDER BY CASE status WHEN 'live' THEN 0 ELSE 1 END, starts_at
        ''').fetchall()
    else:
        matches = conn.execute('''
            SELECT * FROM matches WHERE sport=?
            ORDER BY CASE status WHEN 'live' THEN 0 ELSE 1 END, starts_at
        ''', (sport,)).fetchall()

    stats = {
        'events': conn.execute('SELECT COUNT(*) AS n FROM matches').fetchone()['n'],
        'live': conn.execute("SELECT COUNT(*) AS n FROM matches WHERE status='live'").fetchone()['n'],
        'players': conn.execute('SELECT COUNT(*) AS n FROM users').fetchone()['n'],
    }
    conn.close()
    return render_template('index.html', matches=matches, active_sport=sport, stats=stats)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        conn = db_conn()
        user = conn.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            return redirect(url_for('home'))
        flash('E-mail ou senha inválidos.', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if len(name) < 2:
            flash('Digite seu nome.', 'error')
            return render_template('register.html')
        if len(password) < 6:
            flash('A senha precisa ter pelo menos 6 caracteres.', 'error')
            return render_template('register.html')

        conn = db_conn()
        try:
            cur = conn.execute(
                'INSERT INTO users(name,email,password_hash,score) VALUES(?,?,?,?)',
                (name, email, generate_password_hash(password), 0)
            )
            conn.commit()
            session['user_id'] = cur.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            flash('Este e-mail já está cadastrado.', 'error')
            return render_template('register.html')
        conn.close()
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/make-prediction', methods=['POST'])
def make_prediction():
    user = current_user()
    if not user:
        return jsonify({'ok': False, 'message': 'Faça login para registrar seu palpite.'}), 401

    data = request.get_json(silent=True) or {}
    try:
        match_id = int(data.get('match_id'))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'message': 'Evento inválido.'}), 400
    pick = data.get('pick')

    if pick not in {'home', 'draw', 'away'}:
        return jsonify({'ok': False, 'message': 'Escolha inválida.'}), 400

    conn = db_conn()
    match = conn.execute('SELECT * FROM matches WHERE id=?', (match_id,)).fetchone()
    if not match:
        conn.close()
        return jsonify({'ok': False, 'message': 'Evento não encontrado.'}), 404
    if match['sport'] != 'Futebol' and pick == 'draw':
        conn.close()
        return jsonify({'ok': False, 'message': 'Empate não está disponível para este evento.'}), 400

    try:
        conn.execute('INSERT INTO predictions(user_id,match_id,pick) VALUES(?,?,?)', (user['id'], match_id, pick))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'ok': False, 'message': 'Você já registrou um palpite para este evento.'}), 400

    conn.close()
    return jsonify({'ok': True, 'message': 'Palpite registrado. Nenhum ponto foi gasto.'})


@app.route('/history')
def history():
    user = current_user()
    if not user:
        return redirect(url_for('login'))
    conn = db_conn()
    rows = conn.execute('''
        SELECT p.*, m.home, m.away, m.league, m.sport
        FROM predictions p JOIN matches m ON m.id=p.match_id
        WHERE p.user_id=? ORDER BY p.id DESC
    ''', (user['id'],)).fetchall()
    conn.close()
    return render_template('history.html', rows=rows)


@app.route('/leaderboard')
def leaderboard():
    conn = db_conn()
    rows = conn.execute('SELECT name, score FROM users ORDER BY score DESC, name ASC LIMIT 20').fetchall()
    conn.close()
    return render_template('leaderboard.html', rows=rows)


@app.route('/arcade')
def arcade():
    conn = db_conn()
    best = {}
    user = current_user()
    if user:
        rows = conn.execute(
            'SELECT game, MAX(score) best FROM arcade_scores WHERE user_id=? GROUP BY game',
            (user['id'],)
        ).fetchall()
        best = {r['game']: r['best'] for r in rows}
    conn.close()
    return render_template('arcade.html', best=best)


@app.route('/api/arcade-score', methods=['POST'])
def arcade_score():
    user = current_user()
    if not user:
        return jsonify({'ok': False, 'message': 'Entre na conta para salvar sua pontuação.'}), 401

    data = request.get_json(silent=True) or {}
    game = str(data.get('game', ''))
    try:
        score = int(data.get('score', 0))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'message': 'Pontuação inválida.'}), 400

    limits = {g['key']: g['limit'] for g in ARCADE_GAMES}
    if game not in limits or score < 0 or score > limits[game]:
        return jsonify({'ok': False, 'message': 'Pontuação inválida.'}), 400

    conn = db_conn()
    conn.execute('INSERT INTO arcade_scores(user_id,game,score) VALUES(?,?,?)', (user['id'], game, score))
    bonus = score * 5
    conn.execute('UPDATE users SET score=score+? WHERE id=?', (bonus, user['id']))
    conn.commit()
    total = conn.execute('SELECT score FROM users WHERE id=?', (user['id'],)).fetchone()['score']
    conn.close()
    return jsonify({'ok': True, 'bonus': bonus, 'total': total})


@app.route('/api/settle-demo', methods=['POST'])
def settle_demo():
    user = current_user()
    if not user:
        return jsonify({'ok': False, 'message': 'Faça login.'}), 401
    conn = db_conn()
    p = conn.execute(
        'SELECT * FROM predictions WHERE user_id=? AND status="pending" ORDER BY id LIMIT 1',
        (user['id'],)
    ).fetchone()
    if not p:
        conn.close()
        return jsonify({'ok': False, 'message': 'Nenhum palpite pendente.'}), 400

    won = random.choice([True, False])
    points = 100 if won else 0
    conn.execute(
        'UPDATE predictions SET status=?, points_awarded=? WHERE id=?',
        ('won' if won else 'lost', points, p['id'])
    )
    if won:
        conn.execute('UPDATE users SET score=score+? WHERE id=?', (points, user['id']))
    conn.commit()
    total = conn.execute('SELECT score FROM users WHERE id=?', (user['id'],)).fetchone()['score']
    conn.close()
    return jsonify({'ok': True, 'result': 'won' if won else 'lost', 'points': points, 'total': total})


init_db()

if __name__ == '__main__':
    app.run(debug=True)
