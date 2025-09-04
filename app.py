from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.exceptions import BadRequest
from models.todo import Todo
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
todo = Todo()

# Add template filter for current date
@app.template_filter('today')
def today_filter(s):
    return datetime.now().strftime('%Y-%m-%d')

# Add template context processor to make datetime available
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'today': datetime.now().strftime('%Y-%m-%d')}

@app.route('/')
def index():
    filter_by = request.args.get('filter')
    sort_by = request.args.get('sort', 'priority')
    search_query = request.args.get('search')
    
    if search_query:
        tasks = todo.search_tasks(search_query)
    else:
        tasks = todo.read_tasks(filter_by=filter_by, sort_by=sort_by)
    
    stats = todo.get_statistics()
    categories = todo.get_categories()
    
    return render_template('index.html', 
                         tasks=tasks, 
                         stats=stats, 
                         categories=categories,
                         current_filter=filter_by,
                         current_sort=sort_by,
                         search_query=search_query or '')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/tasks', methods=['POST'])
def create_task():
    try:
        title = request.form.get('title', '').strip()
        priority = request.form.get('priority', 'medium')
        category = request.form.get('category', 'general')
        due_date = request.form.get('due_date') or None
        
        if not title:
            return jsonify({'success': False, 'error': 'Title is required'}), 400
        
        task = todo.create_task(title, priority, category, due_date)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'task': task})
        else:
            return redirect(url_for('index'))
            
    except ValueError as e:
        error_msg = str(e)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': error_msg}), 400
        return redirect(url_for('index'))
    except Exception as e:
        error_msg = 'Failed to create task'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': error_msg}), 500
        return redirect(url_for('index'))

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        data = request.get_json()
        if data is None:
            raise BadRequest('Invalid JSON data')

        result = todo.update_task(task_id, **data)
        
        if result is None:
            return jsonify({'success': False, 'error': 'Task not found'}), 404
            
        return jsonify({'success': True, 'task': result})
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to update task'}), 500

@app.route('/tasks/<int:task_id>', methods=['DELETE', 'POST'])
def delete_task(task_id):
    try:
        success = todo.delete_task(task_id)
        
        if request.method == 'DELETE' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Task not found'}), 404
        else:
            return redirect(url_for('index'))
            
    except Exception as e:
        if request.method == 'DELETE' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Failed to delete task'}), 500
        return redirect(url_for('index'))

@app.route('/tasks/<int:task_id>/details', methods=['GET'])
def get_task_details(task_id):
    task = todo.get_task(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    return jsonify({'success': True, 'task': task})

@app.route('/api/stats')
def get_statistics():
    return jsonify(todo.get_statistics())

@app.route('/api/categories')
def get_categories():
    return jsonify({'categories': todo.get_categories()})

@app.route('/tasks/bulk-delete', methods=['POST'])
def bulk_delete():
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        deleted_count = 0
        for task_id in task_ids:
            if todo.delete_task(task_id):
                deleted_count += 1
        
        return jsonify({
            'success': True, 
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} tasks'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to delete tasks'}), 500

@app.route('/tasks/clear-completed', methods=['POST'])
def clear_completed():
    try:
        deleted_count = todo.delete_completed_tasks()
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} completed tasks'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to clear completed tasks'}), 500

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': str(e)}), 400
    return redirect(url_for('index'))

@app.errorhandler(404)
def handle_not_found(e):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def handle_server_error(e):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)