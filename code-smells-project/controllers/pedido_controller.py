import logging
import sqlite3
from flask import request, jsonify
from services import pedido_service

logger = logging.getLogger(__name__)


def listar_todos_pedidos():
    pedidos = pedido_service.listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_service.listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    try:
        resultado = pedido_service.criar(usuario_id, itens)
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201
    except ValueError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400
    except sqlite3.Error:
        logger.exception("Erro ao criar pedido para usuário %s", usuario_id)
        return jsonify({"erro": "Erro interno"}), 500


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    novo_status = dados.get("status", "")
    try:
        pedido_service.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except sqlite3.Error:
        logger.exception("Erro ao atualizar status do pedido %s", pedido_id)
        return jsonify({"erro": "Erro interno"}), 500


def relatorio_vendas():
    relatorio = pedido_service.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
