import logging
from sqlalchemy.exc import SQLAlchemyError
from database import db
from models.category import Category
from models.task import Task

logger = logging.getLogger(__name__)


class CategoryService:

    @staticmethod
    def get_all():
        categories = Category.query.all()
        result = []
        for category in categories:
            data = category.to_dict()
            data['task_count'] = Task.query.filter_by(category_id=category.id).count()
            result.append(data)
        return result

    @staticmethod
    def create(data):
        name = data.get('name')
        if not name:
            raise ValueError('Nome é obrigatório')
        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')
        try:
            db.session.add(category)
            db.session.commit()
            return category.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error creating category')
            raise

    @staticmethod
    def update(cat_id, data):
        category = Category.query.get(cat_id)
        if not category:
            return None
        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']
        if 'color' in data:
            category.color = data['color']
        try:
            db.session.commit()
            return category.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error updating category')
            raise

    @staticmethod
    def delete(cat_id):
        category = Category.query.get(cat_id)
        if not category:
            return False
        try:
            db.session.delete(category)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error deleting category')
            raise
