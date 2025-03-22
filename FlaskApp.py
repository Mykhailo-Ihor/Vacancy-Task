from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime
import uuid

app = Flask(__name__)

exercises = {}


from datetime import datetime, date

def calculate_status(exercise):
    today = date.today()
    due_date = exercise['due_date'].date()

    if exercise['result']:
        return "DONE"
    elif today > due_date:
        return "MISSED"
    else:
        return "PENDING"

@app.route('/create_exercise', methods=['GET', 'POST'])
def create_exercise():
    if request.method == 'POST':
        client_name = request.form['client_name']
        description = request.form['description']
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')

        exercise_id = str(uuid.uuid4())
        exercises[exercise_id] = {
            'client_name': client_name,
            'description': description,
            'due_date': due_date,
            'result': None,
            'comment': None
        }

        exercise_link = f"{request.host_url}exercise/{exercise_id}"
        return f"Exercise created! Share this link with your client: {exercise_link}"

    return render_template('create_exercise.html')


@app.route('/exercises')
def list_exercises():
    for exercise_id, exercise in exercises.items():
        exercise['status'] = calculate_status(exercise)
    return render_template('exercises.html', exercises=exercises)

@app.route('/exercise/<exercise_id>', methods=['GET', 'POST'])
def view_exercise(exercise_id):
    exercise = exercises.get(exercise_id)
    if not exercise:
        return "Exercise not found!", 404

    if request.method == 'POST':
        exercise['result'] = request.form['result']
        exercise['comment'] = request.form['comment']
        return "Thank you for your feedback!"

    status = calculate_status(exercise)
    today = date.today()
    due_date = exercise['due_date'].date()
    time_to_due = (due_date - today).days

    return render_template('exercise.html', exercise=exercise, status=status, time_to_due=time_to_due)

if __name__ == '__main__':
    app.run(debug=True)