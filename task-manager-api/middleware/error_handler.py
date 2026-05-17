import logging
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': 'Método não permitido'}), 405

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        logger.exception('Unhandled database error')
        return jsonify({'error': 'Erro no banco de dados'}), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        logger.exception('Unhandled exception')
        return jsonify({'error': 'Erro interno do servidor'}), 500
