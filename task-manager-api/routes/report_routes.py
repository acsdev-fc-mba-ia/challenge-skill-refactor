from flask import Blueprint
from controllers.report_controller import summary_report, user_report

report_bp = Blueprint('reports', __name__)

report_bp.route('/reports/summary', methods=['GET'])(summary_report)
report_bp.route('/reports/user/<int:user_id>', methods=['GET'])(user_report)
