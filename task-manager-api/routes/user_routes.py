from flask import Blueprint
from controllers.user_controller import (
    get_users, get_user, create_user, update_user,
    delete_user, get_user_tasks, login
)

user_bp = Blueprint('users', __name__)

user_bp.route('/users', methods=['GET'])(get_users)
user_bp.route('/users/<int:user_id>', methods=['GET'])(get_user)
user_bp.route('/users', methods=['POST'])(create_user)
user_bp.route('/users/<int:user_id>', methods=['PUT'])(update_user)
user_bp.route('/users/<int:user_id>', methods=['DELETE'])(delete_user)
user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])(get_user_tasks)
user_bp.route('/login', methods=['POST'])(login)
