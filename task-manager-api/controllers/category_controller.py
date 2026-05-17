from flask import request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from services.category_service import CategoryService


def get_categories():
    return jsonify(CategoryService.get_all()), 200


def create_category():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    try:
        category = CategoryService.create(data)
        return jsonify(category), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao criar categoria'}), 500


def update_category(cat_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    try:
        category = CategoryService.update(cat_id, data)
        if category is None:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        return jsonify(category), 200
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao atualizar'}), 500


def delete_category(cat_id):
    try:
        found = CategoryService.delete(cat_id)
        if not found:
            return jsonify({'error': 'Categoria não encontrada'}), 404
        return jsonify({'message': 'Categoria deletada'}), 200
    except SQLAlchemyError:
        return jsonify({'error': 'Erro ao deletar'}), 500
