from datetime import datetime
import json
import os

class Todo:
    def __init__(self, data_file='tasks.json'):
        self.data_file = data_file
        self.tasks = []
        self.next_id = 1
        self.load_tasks()

    def load_tasks(self):
        """Load tasks from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.next_id = data.get('next_id', 1)
        except (json.JSONDecodeError, FileNotFoundError):
            self.tasks = []
            self.next_id = 1

    def save_tasks(self):
        """Save tasks to JSON file"""
        try:
            data = {
                'tasks': self.tasks,
                'next_id': self.next_id
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def create_task(self, title, priority='medium', category='general', due_date=None):
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        
        task = {
            'id': self.next_id,
            'title': title.strip(),
            'completed': False,
            'priority': priority,
            'category': category,
            'created_at': datetime.now().isoformat(),
            'due_date': due_date,
            'notes': ''
        }
        self.tasks.append(task)
        self.next_id += 1
        self.save_tasks()
        return task

    def read_tasks(self, filter_by=None, sort_by='priority'):
        """Get tasks with optional filtering and sorting"""
        filtered_tasks = self.tasks.copy()
        
        # Apply filters
        if filter_by:
            if filter_by == 'completed':
                filtered_tasks = [t for t in filtered_tasks if t['completed']]
            elif filter_by == 'pending':
                filtered_tasks = [t for t in filtered_tasks if not t['completed']]
            elif filter_by in ['high', 'medium', 'low']:
                filtered_tasks = [t for t in filtered_tasks if t['priority'] == filter_by]
            elif filter_by.startswith('category:'):
                category = filter_by.split(':')[1]
                filtered_tasks = [t for t in filtered_tasks if t.get('category', 'general') == category]
        
        # Sort tasks
        if sort_by == 'priority':
            priority_order = {'high': 1, 'medium': 2, 'low': 3}
            filtered_tasks.sort(key=lambda x: (x['completed'], priority_order.get(x['priority'], 4)))
        elif sort_by == 'created_at':
            filtered_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        elif sort_by == 'title':
            filtered_tasks.sort(key=lambda x: x['title'].lower())
        elif sort_by == 'due_date':
            filtered_tasks.sort(key=lambda x: x.get('due_date') or '9999-12-31')
        
        return filtered_tasks

    def get_task(self, task_id):
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None

    def update_task(self, task_id, **kwargs):
        task = self.get_task(task_id)
        if not task:
            return None
        
        # Update allowed fields
        allowed_fields = ['title', 'completed', 'priority', 'category', 'due_date', 'notes']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                if field == 'title' and (not value or not value.strip()):
                    raise ValueError("Task title cannot be empty")
                if field == 'completed':
                    task[field] = bool(value)
                else:
                    task[field] = value
        
        self.save_tasks()
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return False
        self.tasks.remove(task)
        self.save_tasks()
        return True

    def get_statistics(self):
        """Get task statistics"""
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks if t['completed']])
        pending_tasks = total_tasks - completed_tasks
        
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        category_counts = {}
        
        for task in self.tasks:
            if not task['completed']:  # Count only pending tasks
                priority_counts[task['priority']] = priority_counts.get(task['priority'], 0) + 1
                category = task.get('category', 'general')
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total': total_tasks,
            'completed': completed_tasks,
            'pending': pending_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'priority_counts': priority_counts,
            'category_counts': category_counts
        }

    def search_tasks(self, query):
        """Search tasks by title or notes"""
        if not query:
            return []
        
        query = query.lower().strip()
        results = []
        
        for task in self.tasks:
            if (query in task['title'].lower() or 
                query in task.get('notes', '').lower()):
                results.append(task)
        
        return results

    def get_categories(self):
        """Get all unique categories"""
        categories = set()
        for task in self.tasks:
            categories.add(task.get('category', 'general'))
        return sorted(list(categories))

    def delete_completed_tasks(self):
        """Delete all completed tasks"""
        initial_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if not t['completed']]
        deleted_count = initial_count - len(self.tasks)
        if deleted_count > 0:
            self.save_tasks()
        return deleted_count