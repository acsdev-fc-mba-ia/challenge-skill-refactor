from flask import jsonify
from services.report_service import ReportService


def summary_report():
    return jsonify(ReportService.summary()), 200


def user_report(user_id):
    report = ReportService.user_report(user_id)
    if report is None:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(report), 200
