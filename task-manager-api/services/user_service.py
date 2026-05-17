import logging
import re
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from database import db
from models.user import User
from models.task import Task
from services.exceptions import ConflictError, AuthenticationError

logger = logging.getLogger(__name__)

VALID_ROLES = ('user', 'admin', 'manager')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


class UserService:

    @staticmethod
    def get_all():
        users = User.query.options(joinedload(User.tasks)).all()
        return [
            {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'active': user.active,
                'created_at': str(user.created_at),
                'task_count': len(user.tasks)
            }
            for user in users
        ]

    @staticmethod
    def get_by_id(user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        data = user.to_dict()
        data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
        return data

    @staticmethod
    def create(data):
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise ValueError('Nome é obrigatório')
        if not email:
            raise ValueError('Email é obrigatório')
        if not password:
            raise ValueError('Senha é obrigatória')
        if not EMAIL_PATTERN.match(email):
            raise ValueError('Email inválido')
        if len(password) < 4:
            raise ValueError('Senha deve ter no mínimo 4 caracteres')
        if role not in VALID_ROLES:
            raise ValueError('Role inválido')
        if User.query.filter_by(email=email).first():
            raise ConflictError('Email já cadastrado')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        try:
            db.session.add(user)
            db.session.commit()
            logger.info('User created: %d - %s', user.id, user.name)
            return user.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error creating user')
            raise

    @staticmethod
    def update(user_id, data):
        user = User.query.get(user_id)
        if not user:
            return None

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not EMAIL_PATTERN.match(data['email']):
                raise ValueError('Email inválido')
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < 4:
                raise ValueError('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValueError('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        try:
            db.session.commit()
            return user.to_dict()
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error updating user')
            raise

    @staticmethod
    def delete(user_id):
        user = User.query.get(user_id)
        if not user:
            return False
        for task in Task.query.filter_by(user_id=user_id).all():
            db.session.delete(task)
        try:
            db.session.delete(user)
            db.session.commit()
            logger.info('User deleted: %d', user_id)
            return True
        except SQLAlchemyError:
            db.session.rollback()
            logger.exception('database error deleting user')
            raise

    @staticmethod
    def get_tasks(user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        result = []
        for task in Task.query.filter_by(user_id=user_id).all():
            data = task.to_dict()
            data['is_overdue'] = task.is_overdue()
            result.append(data)
        return result

    @staticmethod
    def login(email, password):
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise AuthenticationError('Credenciais inválidas')
        if not user.active:
            raise PermissionError('Usuário inativo')
        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': f'fake-jwt-token-{user.id}'
        }
