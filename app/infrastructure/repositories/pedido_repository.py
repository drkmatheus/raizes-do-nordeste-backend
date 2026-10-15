from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import CanalPedido, StatusPedido
from app.domain.models.pedido import Pedido


class PedidoRepository:
    def __init__(self, session: Session):
        self.session = session

    def obterPorId(self, pedidoId: int) -> Pedido | None:
        return self.session.get(Pedido, pedidoId)

    def obterPorIdParaAtualizar(self, pedidoId: int) -> Pedido | None:
        stmt = select(Pedido).where(Pedido.id == pedidoId).with_for_update()
        return self.session.scalars(stmt).one_or_none()

    def obterPorRequestId(self, requestId: str) -> Pedido | None:
        stmt = select(Pedido).where(Pedido.requestId == requestId)
        return self.session.scalars(stmt).one_or_none()

    def listar(self, limite: int = 50, deslocamento: int = 0, canalPedido: CanalPedido | None = None, status: StatusPedido | None = None, clienteId: int | None = None) -> list[Pedido]:
        stmt = select(Pedido)
        if canalPedido is not None:
            stmt = stmt.where(Pedido.canalPedido == canalPedido)
        if status is not None:
            stmt = stmt.where(Pedido.status == status)
        if clienteId is not None:
            stmt = stmt.where(Pedido.clienteId == clienteId)
        stmt = stmt.order_by(Pedido.id.desc()).limit(limite).offset(deslocamento)
        return list(self.session.scalars(stmt))

    def adicionar(self, pedido: Pedido) -> Pedido:
        self.session.add(pedido)
        self.session.flush()
        return pedido
