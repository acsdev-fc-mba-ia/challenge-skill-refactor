import logging
import sqlite3
from flask import request, jsonify
from services import produto_service

logger = logging.getLogger(__name__)


def listar_produtos():
    produtos = produto_service.listar_todos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_service.buscar_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria") or None
        preco_min = float(request.args["preco_min"]) if request.args.get("preco_min") else None
        preco_max = float(request.args["preco_max"]) if request.args.get("preco_max") else None
    except ValueError:
        return jsonify({"erro": "Parâmetros de preço inválidos"}), 400

    resultados = produto_service.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def criar_produto():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if "preco" not in dados:
        return jsonify({"erro": "Preço é obrigatório"}), 400
    if "estoque" not in dados:
        return jsonify({"erro": "Estoque é obrigatório"}), 400

    try:
        produto_id = produto_service.criar(
            nome=dados["nome"],
            descricao=dados.get("descricao", ""),
            preco=dados["preco"],
            estoque=dados["estoque"],
            categoria=dados.get("categoria", "geral"),
        )
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.Error:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": "Erro interno"}), 500


def atualizar_produto(id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400
    if "nome" not in dados:
        return jsonify({"erro": "Nome é obrigatório"}), 400
    if "preco" not in dados:
        return jsonify({"erro": "Preço é obrigatório"}), 400
    if "estoque" not in dados:
        return jsonify({"erro": "Estoque é obrigatório"}), 400

    try:
        atualizado = produto_service.atualizar(
            produto_id=id,
            nome=dados["nome"],
            descricao=dados.get("descricao", ""),
            preco=dados["preco"],
            estoque=dados["estoque"],
            categoria=dados.get("categoria", "geral"),
        )
        if not atualizado:
            return jsonify({"erro": "Produto não encontrado"}), 404
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.Error:
        logger.exception("Erro ao atualizar produto %s", id)
        return jsonify({"erro": "Erro interno"}), 500


def deletar_produto(id):
    deletado = produto_service.deletar(id)
    if not deletado:
        return jsonify({"erro": "Produto não encontrado"}), 404
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
