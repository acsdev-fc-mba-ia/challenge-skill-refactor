CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


class Produto:
    def __init__(self, id, nome, descricao, preco, estoque, categoria, ativo, criado_em):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.preco = preco
        self.estoque = estoque
        self.categoria = categoria
        self.ativo = ativo
        self.criado_em = criado_em

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row['id'], nome=row['nome'], descricao=row['descricao'],
            preco=row['preco'], estoque=row['estoque'], categoria=row['categoria'],
            ativo=row['ativo'], criado_em=row['criado_em'],
        )

    def to_dict(self):
        return {
            'id': self.id, 'nome': self.nome, 'descricao': self.descricao,
            'preco': self.preco, 'estoque': self.estoque, 'categoria': self.categoria,
            'ativo': self.ativo, 'criado_em': self.criado_em,
        }
