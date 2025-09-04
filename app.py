from flask import Flask, render_template, request, redirect, url_for, jsonify
from models.todo import Todo
import os

app = Flask(__name__)
todo = Todo()

@app.route('/')
def index():
    return render_template('index.html', tasks=todo.read_tasks())

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/tasks', methods=['POST'])
def create_task():
    title = request.form.get('task')
    priority = request.form.get('priority', 'medium')
    todo.create_task(title, priority)
    return redirect(url_for('index'))

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    result = todo.update_task(
        task_id,
        data.get('title'),
        data.get('completed'),
        data.get('priority')
    )
    if result is None:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    return jsonify({'success': True})

@app.route('/tasks/<int:task_id>', methods=['DELETE', 'POST'])
def delete_task(task_id):
    if todo.delete_task(task_id):
        return redirect(url_for('index'))
    return redirect(url_for('index')), 404

if __name__ == "__main__":
    app.run(debug=False)
