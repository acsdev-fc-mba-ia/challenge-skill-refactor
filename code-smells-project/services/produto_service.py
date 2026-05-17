import logging
import sqlite3
from database import get_db
from models.produto import Produto, CATEGORIAS_VALIDAS

logger = logging.getLogger(__name__)


def listar_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    return [Produto.from_row(row).to_dict() for row in cursor.fetchall()]


def buscar_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return Produto.from_row(row).to_dict() if row else None


def buscar(termo='', categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f'%{termo}%', f'%{termo}%'])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)
    cursor.execute(query, params)
    return [Produto.from_row(row).to_dict() for row in cursor.fetchall()]


def _validar_produto(nome, preco, estoque, categoria):
    if len(nome) < 2:
        raise ValueError("Nome muito curto")
    if len(nome) > 200:
        raise ValueError("Nome muito longo")
    if preco < 0:
        raise ValueError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValueError("Estoque não pode ser negativo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")


def criar(nome, descricao, preco, estoque, categoria):
    _validar_produto(nome, preco, estoque, categoria)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    logger.info("Produto criado com ID %s", cursor.lastrowid)
    return cursor.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    _validar_produto(nome, preco, estoque, categoria)
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM produtos WHERE id = ?", (produto_id,))
    if not cursor.fetchone():
        return False
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def deletar(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM produtos WHERE id = ?", (produto_id,))
    if not cursor.fetchone():
        return False
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    logger.info("Produto %s deletado", produto_id)
    return True
