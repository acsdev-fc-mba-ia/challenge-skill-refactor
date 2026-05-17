import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import joinedload
from models.task import Task
from models.user import User
from models.category import Category

logger = logging.getLogger(__name__)


class ReportService:

    @staticmethod
    def summary():
        now = datetime.now(timezone.utc)
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        priority_counts = {p: Task.query.filter_by(priority=p).count() for p in range(1, 6)}

        overdue_list = []
        for task in Task.query.all():
            if task.is_overdue():
                overdue_list.append({
                    'id': task.id,
                    'title': task.title,
                    'due_date': str(task.due_date),
                    'days_overdue': (now - task.due_date.replace(tzinfo=timezone.utc)).days
                })

        seven_days_ago = now - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago
        ).count()

        users = User.query.options(joinedload(User.tasks)).all()
        user_stats = []
        for user in users:
            total = len(user.tasks)
            completed = sum(1 for t in user.tasks if t.status == 'done')
            user_stats.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
            })

        return {
            'generated_at': str(now),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                'critical': priority_counts[1],
                'high': priority_counts[2],
                'medium': priority_counts[3],
                'low': priority_counts[4],
                'minimal': priority_counts[5],
            },
            'overdue': {
                'count': len(overdue_list),
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    @staticmethod
    def user_report(user_id):
        user = User.query.get(user_id)
        if not user:
            return None

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        done = pending = in_progress = cancelled = overdue = high_priority = 0

        for task in tasks:
            if task.status == 'done':
                done += 1
            elif task.status == 'pending':
                pending += 1
            elif task.status == 'in_progress':
                in_progress += 1
            elif task.status == 'cancelled':
                cancelled += 1
            if task.priority <= 2:
                high_priority += 1
            if task.is_overdue():
                overdue += 1

        return {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
            }
        }
