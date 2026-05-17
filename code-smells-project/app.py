import logging
from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import SECRET_KEY, DEBUG, HOST, PORT
from database import init_db, get_db
from middleware.error_handler import register_error_handlers
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp
from routes.pedido_routes import pedido_bp

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG
CORS(app)

app.register_blueprint(produto_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(pedido_bp)
register_error_handlers(app)

init_db(app)


@app.route('/')
def index():
    return jsonify({
        'mensagem': 'Bem-vindo à API da Loja',
        'versao': '2.0.0',
        'endpoints': {
            'produtos': '/produtos',
            'usuarios': '/usuarios',
            'pedidos': '/pedidos',
            'login': '/login',
            'relatorios': '/relatorios/vendas',
            'health': '/health',
        },
    })


@app.route('/health')
def health_check():
    import sqlite3
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        produtos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        pedidos = cursor.fetchone()[0]
        return jsonify({
            'status': 'ok',
            'database': 'connected',
            'counts': {'produtos': produtos, 'usuarios': usuarios, 'pedidos': pedidos},
            'versao': '2.0.0',
        }), 200
    except sqlite3.Error:
        logging.exception("Health check database error")
        return jsonify({'status': 'erro'}), 500


if __name__ == '__main__':
    print('=' * 50)
    print('SERVIDOR INICIADO')
    print(f'Rodando em http://{HOST}:{PORT}')
    print('=' * 50)
    app.run(host=HOST, port=PORT, debug=DEBUG)
