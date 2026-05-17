import logging
import sqlite3
from database import get_db
from models.pedido import STATUS_VALIDOS, DISCOUNT_TIERS

logger = logging.getLogger(__name__)


def _build_pedidos_from_join(rows):
    pedidos: dict = {}
    for row in rows:
        pedido_id = row['pedido_id']
        if pedido_id not in pedidos:
            pedidos[pedido_id] = {
                'id': pedido_id,
                'usuario_id': row['usuario_id'],
                'status': row['status'],
                'total': row['total'],
                'criado_em': row['criado_em'],
                'itens': [],
            }
        if row['produto_id'] is not None:
            pedidos[pedido_id]['itens'].append({
                'produto_id': row['produto_id'],
                'produto_nome': row['produto_nome'] or 'Desconhecido',
                'quantidade': row['quantidade'],
                'preco_unitario': row['preco_unitario'],
            })
    return list(pedidos.values())


_JOIN_QUERY = """
    SELECT
        p.id   AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
        ip.produto_id, ip.quantidade, ip.preco_unitario,
        pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos      pr ON pr.id = ip.produto_id
"""


def listar_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(_JOIN_QUERY + " ORDER BY p.id")
    return _build_pedidos_from_join(cursor.fetchall())


def listar_por_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(_JOIN_QUERY + " WHERE p.usuario_id = ? ORDER BY p.id", (usuario_id,))
    return _build_pedidos_from_join(cursor.fetchall())


def criar(usuario_id, itens):
    db = get_db()
    cursor = db.cursor()
    total = 0.0

    for item in itens:
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (item['produto_id'],))
        produto = cursor.fetchone()
        if produto is None:
            raise ValueError(f"Produto {item['produto_id']} não encontrado")
        if produto['estoque'] < item['quantidade']:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        total += produto['preco'] * item['quantidade']

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, 'pendente', total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute("SELECT preco FROM produtos WHERE id = ?", (item['produto_id'],))
        produto = cursor.fetchone()
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item['produto_id'], item['quantidade'], produto['preco']),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item['quantidade'], item['produto_id']),
        )

    db.commit()
    logger.info("Pedido %s criado para usuário %s — total R$%.2f", pedido_id, usuario_id, total)
    return {'pedido_id': pedido_id, 'total': total}


def atualizar_status(pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ValueError(f"Status inválido. Válidos: {STATUS_VALIDOS}")
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    logger.info("Pedido %s → status %s", pedido_id, novo_status)


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    desconto = _calcular_desconto(faturamento)
    return {
        'total_pedidos': total_pedidos,
        'faturamento_bruto': round(faturamento, 2),
        'desconto_aplicavel': round(desconto, 2),
        'faturamento_liquido': round(faturamento - desconto, 2),
        'pedidos_pendentes': pendentes,
        'pedidos_aprovados': aprovados,
        'pedidos_cancelados': cancelados,
        'ticket_medio': round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def _calcular_desconto(faturamento):
    for threshold, rate in DISCOUNT_TIERS:
        if faturamento > threshold:
            return faturamento * rate
    return 0.0
