from flask import Blueprint
from controllers.category_controller import (
    get_categories, create_category, update_category, delete_category
)

category_bp = Blueprint('categories', __name__)

category_bp.route('/categories', methods=['GET'])(get_categories)
category_bp.route('/categories', methods=['POST'])(create_category)
category_bp.route('/categories/<int:cat_id>', methods=['PUT'])(update_category)
category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])(delete_category)
