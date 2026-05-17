import logging
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from database import db
from models.task import Task
from models.user import User
from models.category import Category

logger = logging.getLogger(__name__)

VALID_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')


class TaskService:

    @staticmethod
    def get_all():
        tasks = Task.query.options(
            joinedload(Task.user),
            joinedload(Task.category)
        ).all()
        result = []
        for task in tasks:
            data = task.to_dict()
            data['is_overdue'] = task.is_overdue()
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
            result.append(data)
        return result

    @staticmethod
    def get_by_id(task_id):
        task = Task.query.get(task_id)
        if not task:
            return None
        data = task.to_dict()
        data['is_overdue'] = task.is_overdue()
        return data

    @staticmethod
    def create(data):
        title = data.get('title')
        if not title:
            raise ValueError('Título é obrigatório')
        title = title.strip()
        if len(title) < 3:
            raise ValueError('Título muito curto')
        if len(title) > 200:
            raise ValueError('Título muito longo')

        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            raise ValueError('Status inválido')

        priority = data.get('priority', 3)
        if priority < 1 or priority > 5:
            raise ValueError('Prioridade deve ser entre 1 e 5')

        user_id = data.get('user_id')
        if user_id and not User.query.get(user_id):
            raise LookupError('Usuário não encontrado')

        category_id = data.get('category_id')
        if category_id and not Category.query.get(category_id):
            raise LookupError('Categoria não encontrada')

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        due_date_str = data.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Formato de data inválido. Use YYYY-MM-DD')

        tags = data.get('tags')
        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        try:
            db.session.add(task)
            db.session.commit()
            logger.info('Task created: %d - %s', task.id, task.title)
            return task.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error creating task')
            raise

    @staticmethod
    def update(task_id, data):
        task = Task.query.get(task_id)
        if not task:
            return None

        if 'title' in data:
            title = data['title']
            if len(title) < 3:
                raise ValueError('Título muito curto')
            if len(title) > 200:
                raise ValueError('Título muito longo')
            task.title = title

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                raise ValueError('Status inválido')
            task.status = data['status']

        if 'priority' in data:
            if data['priority'] < 1 or data['priority'] > 5:
                raise ValueError('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id'] and not User.query.get(data['user_id']):
                raise LookupError('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not Category.query.get(data['category_id']):
                raise LookupError('Categoria não encontrada')
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
                except ValueError:
                    raise ValueError('Formato de data inválido')
            else:
                task.due_date = None

        if 'tags' in data:
            tags = data['tags']
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        try:
            db.session.commit()
            logger.info('Task updated: %d', task.id)
            return task.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error updating task')
            raise

    @staticmethod
    def delete(task_id):
        task = Task.query.get(task_id)
        if not task:
            return False
        try:
            db.session.delete(task)
            db.session.commit()
            logger.info('Task deleted: %d', task_id)
            return True
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error deleting task')
            raise

    @staticmethod
    def search(query='', status='', priority='', user_id=''):
        q = Task.query
        if query:
            q = q.filter(db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            ))
        if status:
            q = q.filter(Task.status == status)
        if priority:
            q = q.filter(Task.priority == int(priority))
        if user_id:
            q = q.filter(Task.user_id == int(user_id))
        return [task.to_dict() for task in q.all()]

    @staticmethod
    def stats():
        total = Task.query.count()
        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()
        overdue_count = sum(1 for t in Task.query.all() if t.is_overdue())
        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
        }
