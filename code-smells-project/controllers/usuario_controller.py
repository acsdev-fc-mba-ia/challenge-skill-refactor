import logging
import sqlite3
from flask import request, jsonify
from services import usuario_service

logger = logging.getLogger(__name__)


def listar_usuarios():
    usuarios = usuario_service.listar_todos()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_service.buscar_por_id(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    try:
        usuario_id = usuario_service.criar(nome, email, senha)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Email já cadastrado"}), 409
    except sqlite3.Error:
        logger.exception("Erro ao criar usuário")
        return jsonify({"erro": "Erro interno"}), 500


def login():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = usuario_service.autenticar(email, senha)
    if not usuario:
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
