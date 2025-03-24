from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import uuid
import secrets
app = Flask(__name__)

exercises = {}

from datetime import datetime, date
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
        exercises[exercise_id] = {
            'client_name': client_name,
            'description': description,
            'due_date': due_date,
            'result': None,
            'comment': None,
            'token': token
        }

        exercise_link = f"{request.host_url}exercise/{exercise_id}/{token}"
        return render_template('exercise_created.html', exercise_link=exercise_link)

    return render_template('create_exercise.html', min_date = date.today().isoformat())


@app.route('/exercises')
def list_exercises():
    for exercise_id, exercise in exercises.items():
        exercise['status'] = calculate_status(exercise)
    return render_template('exercises.html', exercises=exercises)

@app.route('/exercise/<exercise_id>/<token>', methods=['GET', 'POST'])
def view_exercise(exercise_id,token):
    exercise = exercises.get(exercise_id)
    if not exercise or exercise.get('token') != token:
        return render_template('exercise_not_found.html'), 404

    if request.method == 'POST':
        exercise['result'] = request.form['result']
        exercise['comment'] = request.form['comment']
        return redirect(url_for('feedback_submitted'))

    if exercise.get('result'):
        return render_template('exercise_completed.html', exercise=exercise)

    status = calculate_status(exercise)
    today = date.today()
    due_date = exercise['due_date'].date()
    time_to_due = (due_date - today).days

    return render_template('exercise.html', exercise=exercise, status=status, time_to_due=time_to_due)

@app.route('/exercise_details/<exercise_id>/<token>')
def exercise_details(exercise_id, token):
    exercise = exercises.get(exercise_id)
    if not exercise or exercise.get('token') != token:
        return "Exercise not found!", 404

    exercise_link = f"{request.host_url}exercise/{exercise_id}/{token}"
    return render_template('exercise_details.html', exercise=exercise, exercise_link=exercise_link)


if __name__ == '__main__':
    app.run(debug=True)