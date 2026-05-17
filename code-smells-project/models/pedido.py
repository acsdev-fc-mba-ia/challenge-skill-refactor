STATUS_VALIDOS = ['pendente', 'aprovado', 'enviado', 'entregue', 'cancelado']

DISCOUNT_TIERS = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]


class Pedido:
    def __init__(self, id, usuario_id, status, total, criado_em, itens=None):
        self.id = id
        self.usuario_id = usuario_id
        self.status = status
        self.total = total
        self.criado_em = criado_em
        self.itens = itens or []

    @classmethod
    def from_row(cls, row, itens=None):
        return cls(
            id=row['id'], usuario_id=row['usuario_id'], status=row['status'],
            total=row['total'], criado_em=row['criado_em'], itens=itens,
        )

    def to_dict(self):
        return {
            'id': self.id, 'usuario_id': self.usuario_id, 'status': self.status,
            'total': self.total, 'criado_em': self.criado_em, 'itens': self.itens,
        }
