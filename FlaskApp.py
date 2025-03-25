from flask import Flask, request, render_template, redirect, url_for,g
from datetime import datetime, date
import uuid
import secrets
import sqlite3
from contextlib import closing

app = Flask(__name__)
app.config['DATABASE'] = 'exercises.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    with closing(get_db()) as db:
        with app.open_resource('exercises.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def generate_token():
    return secrets.token_urlsafe(16)

def calculate_status(exercise):
    today = date.today()
    due_date = exercise['due_date'].date()

    if exercise['result']:
        return "DONE"
    elif today > due_date:
        return "MISSED"
    else:
        return "PENDING"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/feedback_submitted')
def feedback_submitted():
    return render_template('feedback_submitted.html')

@app.route('/create_exercise', methods=['GET', 'POST'])
def create_exercise():
    if request.method == 'POST':
        client_name = request.form['client_name']
        description = request.form['description']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        exercise_id = str(uuid.uuid4())
        token = generate_token()
        with closing(get_db()) as db:
            db.execute('INSERT INTO exercises (id, client_name, description, due_date, token) VALUES (?, ?, ?, ?, ?)', (exercise_id, client_name, description, due_date, token))
            db.commit()

        return redirect(url_for('exercise_created', exercise_id=exercise_id, token=token))

    return render_template('create_exercise.html', min_date = date.today().isoformat())


@app.route('/exercises')
def list_exercises():
    with closing(get_db()) as db:
        exercises = db.execute('SELECT * FROM exercises').fetchall()

    exercises_dict = {}
    for row in exercises:
        exercises_dict[row['id']] = {
            'client_name': row['client_name'],
            'description': row['description'],
            'due_date': datetime.fromisoformat(row['due_date']),
            'result': row['result'],
            'comment': row['comment'],
            'token': row['token'],
            'status': calculate_status({
                'due_date': datetime.fromisoformat(row['due_date']),
                'result': row['result']
            })
        }
    return render_template('exercises.html', exercises=exercises_dict)

@app.route('/exercise/<exercise_id>/<token>', methods=['GET', 'POST'])
def view_exercise(exercise_id,token):
    db = get_db()
    exercise = db.execute('SELECT * FROM exercises WHERE id = ? AND token = ?', (exercise_id,token)).fetchone()

    if not exercise:
        return render_template('exercise_not_found.html'), 404

    exercise_data = {
        'client_name': exercise['client_name'],
        'description': exercise['description'],
        'due_date': datetime.fromisoformat(exercise['due_date']),
        'result': exercise['result'],
        'comment': exercise['comment'],
        'token': token,
        'id': exercise_id
    }
    if request.method == 'POST':
        db.execute("UPDATE exercises SET result = ?, comment = ? WHERE id = ? AND token = ?", (request.form['result'], request.form['comment'], exercise_id,token))
        db.commit()
        return redirect(url_for('feedback_submitted'))

    if exercise_data['result']:
        return render_template('exercise_completed.html', exercise=exercise_data)

    status = calculate_status(exercise_data)
    today = date.today()
    due_date = exercise_data['due_date'].date()
    time_to_due = (due_date - today).days

    return render_template('exercise.html', exercise=exercise_data, status=status, time_to_due=time_to_due, due_date=due_date)

@app.route('/exercise_details/<exercise_id>/<token>')
def exercise_details(exercise_id, token):
    db = get_db()

    exercise_row = db.execute('SELECT * FROM exercises WHERE id = ? AND token = ?', (exercise_id,token)).fetchone()
    if not exercise_row:
        return render_template('exercise_not_found.html'), 404

    exercise_data = {
        'client_name': exercise_row['client_name'],
        'description': exercise_row['description'],
        'due_date': datetime.fromisoformat(exercise_row['due_date']),
        'result': exercise_row['result'],
        'comment': exercise_row['comment'],
        'token': exercise_row['token'],
        'id': exercise_id,
        'status': calculate_status({
            'due_date': datetime.fromisoformat(exercise_row['due_date']),
            'result': exercise_row['result']
        })
    }
    exercise_link = f"{request.host_url}exercise/{exercise_id}/{token}"
    return render_template('exercise_details.html', exercise=exercise_data, exercise_link=exercise_link, exercise_id = exercise_id)

@app.route('/exercise_created/<exercise_id>/<token>')
def exercise_created(exercise_id, token):
    exercise_link = f"{request.host_url}exercise/{exercise_id}/{token}"
    return render_template('exercise_created.html', exercise_link=exercise_link)


@app.route('/delete_exercise/<exercise_id>/<token>', methods=['POST'])
def delete_exercise(exercise_id,token):
    db = get_db()
    exercise = db.execute(
        'SELECT * FROM exercises WHERE id = ? AND token = ?',
        (exercise_id, token)
    ).fetchone()

    if exercise:
        db.execute(
            "DELETE FROM exercises WHERE id = ? AND token = ?",
            (exercise_id, token)
        )
        db.commit()
        return redirect(url_for('list_exercises'))

    return render_template('exercise_not_found.html'), 404

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)