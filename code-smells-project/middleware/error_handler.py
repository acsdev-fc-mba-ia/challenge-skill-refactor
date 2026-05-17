import logging
import sqlite3
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"erro": "Método não permitido", "sucesso": False}), 405

    @app.errorhandler(sqlite3.Error)
    def database_error(e):
        logger.exception("Database error")
        return jsonify({"erro": "Erro interno de banco de dados", "sucesso": False}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.exception("Unhandled exception")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
