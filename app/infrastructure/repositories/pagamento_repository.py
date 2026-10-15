from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.pagamento import Pagamento


class PagamentoRepository:
    def __init__(self, session: Session):
        self.session = session

    def obterPorId(self, pagamentoId: int) -> Pagamento | None:
        return self.session.get(Pagamento, pagamentoId)

    def listarPorPedido(self, pedidoId: int) -> list[Pagamento]:
        stmt = (
            select(Pagamento)
            .where(Pagamento.pedidoId == pedidoId)
            .order_by(Pagamento.id)
        )
        return list(self.session.scalars(stmt))

    def adicionar(self, pagamento: Pagamento) -> Pagamento:
        self.session.add(pagamento)
        self.session.flush()
        return pagamento
