from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.unidade import Unidade


class UnidadeRepository:
    def __init__(self, session: Session):
        self.session = session

    def obterPorId(self, unidadeId: int) -> Unidade | None:
        return self.session.get(Unidade, unidadeId)

    def listar(self, limite: int = 50, deslocamento: int = 0) -> list[Unidade]:
        stmt = select(Unidade).order_by(Unidade.id).limit(limite).offset(deslocamento)
        return list(self.session.scalars(stmt))

    def adicionar(self, unidade: Unidade) -> Unidade:
        self.session.add(unidade)
        self.session.flush()
        return unidade
