import logging
import sqlite3
import bcrypt
from database import get_db
from models.usuario import Usuario

logger = logging.getLogger(__name__)


def listar_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [Usuario.from_row(row).to_dict() for row in cursor.fetchall()]


def buscar_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
        (usuario_id,),
    )
    row = cursor.fetchone()
    return Usuario.from_row(row).to_dict() if row else None


def criar(nome, email, senha):
    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, 'cliente'),
    )
    db.commit()
    logger.info("Usuário criado: %s", email)
    return cursor.lastrowid


def autenticar(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if not row:
        return None
    senha_armazenada = row['senha']
    senha_valida = False
    if senha_armazenada.startswith('$2b$') or senha_armazenada.startswith('$2a$'):
        senha_valida = bcrypt.checkpw(senha.encode('utf-8'), senha_armazenada.encode('utf-8'))
    else:
        senha_valida = (senha == senha_armazenada)
    if not senha_valida:
        return None
    logger.info("Login bem-sucedido: %s", email)
    return Usuario.from_row(row).to_dict()
