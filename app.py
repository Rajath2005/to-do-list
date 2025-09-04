# How to access the API key in your Flask app:
# In your Python code, use the os module to read the environment variable, for example:
#
# import os
# api_key = os.getenv('API_KEY')
#
# This way, your app dynamically reads the key at runtime without exposing it in code or repository.

from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.exceptions import BadRequest
from models.todo import Todo
from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()  # Loads environment variables from .env file

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', '')
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

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'success': False, 'response': 'Message is required.'}), 400

        # Include tasks in context
        tasks = todo.read_tasks()
        task_context = "\n".join(
            [f"- {t['title']} (priority: {t['priority']}, completed: {t['completed']})"
             for t in tasks]
        )
        # Enhanced prompt for structured response and JSON command
        prompt = f"""
You are a To-Do List assistant.
Always reply in **two parts**:
1. A natural language response for the user, using:
   - Bullet points for tasks
   - **Bold** for task titles
   - '✅' for completed, '⏳' for pending
2. A JSON object on a new line starting with '###JSON###' that specifies the action.

Valid actions:
- add {{"title": "...", "priority": "high/medium/low", "completed": true/false}}
- complete {{"id": 1}}
- delete {{"id": 1}}
- list {{}}

User's current tasks:
{task_context}

User query: {user_message}
"""

        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
        GEMINI_MODEL = "gemini-1.5-flash"
        GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/{GEMINI_MODEL}:generateContent"

        if not GEMINI_API_KEY:
            return jsonify({'success': False, 'response': 'Gemini API key is not set in .env'}), 500

        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        r = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers,
            json=payload,
            timeout=15
        )
        r.raise_for_status()
        gemini_data = r.json()

        candidates = gemini_data.get('candidates', [])
        response_text = None
        if candidates:
            parts = candidates[0].get('content', {}).get('parts', [])
            if parts and 'text' in parts[0]:
                response_text = parts[0]['text']

        if response_text:
            import json
            raw_text = response_text
            # Look for JSON command
            action = None
            if "###JSON###" in raw_text:
                parts = raw_text.split("###JSON###")
                user_reply = parts[0].strip()
                try:
                    action = json.loads(parts[1].strip())
                except Exception:
                    action = None
            else:
                user_reply = raw_text

            # If AI suggested an action
            if action:
                if action.get("action") == "add":
                    title = action.get("title")
                    priority = action.get("priority", "medium")
                    completed = action.get("completed", False)
                    todo.create_task(title, priority, "general", None)
                    # Add styled HTML for success message
                    user_reply += (
                        f"<div class='ai-success'>"
                        f"<span class='ai-icon'>✅</span> "
                        f"<span class='ai-task-title'>{title}</span> "
                        f"<span class='ai-task-priority {priority}'>{priority.capitalize()} priority</span> "
                        f"added successfully!"
                        f"</div>"
                    )

            # Wrap AI reply in a styled container
            formatted_response = (
                f"<div class='ai-response ai-todo-list'>"
                f"{user_reply.replace(chr(10), '<br>')}"
                f"</div>"
            )
            return jsonify({
                'success': True,
                'response': formatted_response,
                'action': action
            })
        else:
            error_msg = gemini_data.get('error', {}).get('message', "Gemini returned no response")
            return jsonify({'success': False, 'response': f'Gemini API error: {error_msg}'}), 400

    except Exception as e:
        return jsonify({'success': False, 'response': f'Error: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)