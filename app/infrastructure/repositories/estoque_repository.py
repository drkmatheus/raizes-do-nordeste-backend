from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.estoque import Estoque


class EstoqueRepository:
    def __init__(self, session: Session):
        self.session = session

    def obterPorId(self, estoqueId: int) -> Estoque | None:
        return self.session.get(Estoque, estoqueId)

    def obter(self, unidadeId: int, produtoId: int) -> Estoque | None:
        stmt = select(Estoque).where(
            Estoque.unidadeId == unidadeId, Estoque.produtoId == produtoId
        )
        return self.session.scalars(stmt).one_or_none()

    def obterParaAtualizar(self, unidadeId: int, produtoId: int) -> Estoque | None:
        # SELECT ... FOR UPDATE: evita race condition/problema de idempotência em operações de baixa/reposicao de estoque
        stmt = (
            select(Estoque)
            .where(Estoque.unidadeId == unidadeId, Estoque.produtoId == produtoId)
            .with_for_update()
        )
        return self.session.scalars(stmt).one_or_none()

    def listarPorUnidade(self, unidadeId: int, limite: int = 50,
                         deslocamento: int = 0) -> list[Estoque]:
        stmt = (
            select(Estoque)
            .where(Estoque.unidadeId == unidadeId)
            .order_by(Estoque.id)
            .limit(limite)
            .offset(deslocamento)
        )
        return list(self.session.scalars(stmt))

    def adicionar(self, estoque: Estoque) -> Estoque:
        self.session.add(estoque)
        self.session.flush()
        return estoque
