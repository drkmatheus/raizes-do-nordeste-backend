from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.produto import Produto


class ProdutoRepository:
    def __init__(self, session: Session):
        self.session = session

    def obterPorId(self, produtoId: int) -> Produto | None:
        return self.session.get(Produto, produtoId)

    def listar(self, limite: int = 50, deslocamento: int = 0,
               apenasAtivos: bool = False) -> list[Produto]:
        stmt = select(Produto).order_by(Produto.id)
        if apenasAtivos:
            stmt = stmt.where(Produto.ativo.is_(True))
        stmt = stmt.limit(limite).offset(deslocamento)
        return list(self.session.scalars(stmt))

    def adicionar(self, produto: Produto) -> Produto:
        self.session.add(produto)
        self.session.flush()
        return produto
