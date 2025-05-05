from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)


# Инициализация БД
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER,
            text TEXT NOT NULL,
            votes INTEGER DEFAULT 0,
            FOREIGN KEY (poll_id) REFERENCES polls (id)
        )
    ''')

    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM polls')
    polls = c.fetchall()
    conn.close()
    return render_template('index.html', polls=polls)


@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        question = request.form['question']
        options = [opt for opt in request.form.getlist('options') if opt.strip()]

        if not question or len(options) < 2:
            return "Нужен вопрос и минимум 2 варианта", 400

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(
            'INSERT INTO polls (question, created_at) VALUES (?, ?)',
            (question, datetime.now().isoformat())
        )
        poll_id = c.lastrowid

        for opt in options:
            c.execute(
                'INSERT INTO options (poll_id, text) VALUES (?, ?)',
                (poll_id, opt)
            )

        conn.commit()
        conn.close()
        return redirect(url_for('poll', poll_id=poll_id))

    return render_template('create.html')


@app.route('/poll/<int:poll_id>')
def poll(poll_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT question FROM polls WHERE id = ?', (poll_id,))
    poll = c.fetchone()

    c.execute('SELECT id, text FROM options WHERE poll_id = ?', (poll_id,))
    options = c.fetchall()

    conn.close()

    if not poll:
        return "Опрос не найден", 404

    return render_template('poll.html', poll=poll, options=options, poll_id=poll_id)


@app.route('/vote/<int:poll_id>', methods=['POST'])
def vote(poll_id):
    option_id = request.form.get('option')

    if not option_id:
        return "Выберите вариант", 400

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        'UPDATE options SET votes = votes + 1 WHERE id = ?',
        (option_id,)
    )

    conn.commit()
    conn.close()
    return redirect(url_for('results', poll_id=poll_id))


@app.route('/results/<int:poll_id>')
def results(poll_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('SELECT question FROM polls WHERE id = ?', (poll_id,))
    poll = c.fetchone()

    c.execute(
        'SELECT text, votes FROM options WHERE poll_id = ? ORDER BY votes DESC',
        (poll_id,)
    )
    options = c.fetchall()

    total_votes = sum(opt[1] for opt in options)

    conn.close()
    return render_template('results.html',
                           poll=poll,
                           options=options,
                           total_votes=total_votes)


if __name__ == '__main__':
    app.run(debug=True)