import logging
from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from services.task_service import TaskService

logger = logging.getLogger(__name__)


def get_tasks():
    return jsonify(TaskService.get_all()), 200


def get_task(task_id):
    task = TaskService.get_by_id(task_id)
    if task is None:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task), 200


def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    try:
        task = TaskService.create(data)
        return jsonify(task), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except LookupError as e:
        return jsonify({'error': str(e)}), 404
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao criar task'}), 500


def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    try:
        task = TaskService.update(task_id, data)
        if task is None:
            return jsonify({'error': 'Task não encontrada'}), 404
        return jsonify(task), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except LookupError as e:
        return jsonify({'error': str(e)}), 404
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao atualizar'}), 500


def delete_task(task_id):
    try:
        found = TaskService.delete(task_id)
        if not found:
            return jsonify({'error': 'Task não encontrada'}), 404
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao deletar'}), 500


def search_tasks():
    return jsonify(TaskService.search(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', '')
    )), 200


def task_stats():
    return jsonify(TaskService.stats()), 200
