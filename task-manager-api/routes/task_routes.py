from flask import Blueprint
from controllers.task_controller import (
    get_tasks, get_task, create_task, update_task,
    delete_task, search_tasks, task_stats
)

task_bp = Blueprint('tasks', __name__)

task_bp.route('/tasks', methods=['GET'])(get_tasks)
task_bp.route('/tasks/search', methods=['GET'])(search_tasks)
task_bp.route('/tasks/stats', methods=['GET'])(task_stats)
task_bp.route('/tasks/<int:task_id>', methods=['GET'])(get_task)
task_bp.route('/tasks', methods=['POST'])(create_task)
task_bp.route('/tasks/<int:task_id>', methods=['PUT'])(update_task)
task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])(delete_task)
