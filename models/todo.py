class Todo:
    def __init__(self):
        self.tasks = []
        self.next_id = 1  # auto-increment id to avoid re-use after deletes

    def create_task(self, title, priority='medium'):
        task = {
            'id': self.next_id,
            'title': title,
            'completed': False,
            'priority': priority  # high, medium, low
        }
        self.tasks.append(task)
        self.next_id += 1
        return task

    def read_tasks(self):
        # Sort tasks by priority (high > medium > low)
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        return sorted(self.tasks, key=lambda x: priority_order.get(x['priority'], 4))

    def get_task(self, task_id):
        for t in self.tasks:
            if t['id'] == task_id:
                return t
        return None

    def update_task(self, task_id, new_title=None, completed=None, priority=None):
        task = self.get_task(task_id)
        if not task:
            return None
        if new_title is not None and new_title != "":
            task['title'] = new_title
        if completed is not None:
            task['completed'] = bool(completed)
        if priority in ['high', 'medium', 'low']:
            task['priority'] = priority
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        if not task:
            return False
        self.tasks.remove(task)
        return True
