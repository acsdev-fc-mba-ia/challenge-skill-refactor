import logging
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from services.user_service import UserService
from services.exceptions import ConflictError, AuthenticationError

logger = logging.getLogger(__name__)


def get_users():
    return jsonify(UserService.get_all()), 200


def get_user(user_id):
    user = UserService.get_by_id(user_id)
    if user is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(user), 200


def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    try:
        user = UserService.create(data)
        return jsonify(user), 201
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao criar usuário'}), 500


def update_user(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    try:
        user = UserService.update(user_id, data)
        if user is None:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        return jsonify(user), 200
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao atualizar'}), 500


def delete_user(user_id):
    try:
        found = UserService.delete(user_id)
        if not found:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao deletar'}), 500


def get_user_tasks(user_id):
    tasks = UserService.get_tasks(user_id)
    if tasks is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(tasks), 200


def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    try:
        result = UserService.login(email, password)
        return jsonify(result), 200
    except AuthenticationError as e:
        return jsonify({'error': str(e)}), 401
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
