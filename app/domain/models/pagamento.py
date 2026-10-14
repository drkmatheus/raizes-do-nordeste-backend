from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base
from app.domain.enums import StatusPagamento


class Pagamento(Base):
    """ Pagamento desacoplado do pedido: um pedido pode gerar várias tentativas."""

    __tablename__ = "pagamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedidoId: Mapped[int] = mapped_column("pedido_id", ForeignKey("pedido.id"), index=True)
    metodo: Mapped[str] = mapped_column(String(30))
    status: Mapped[StatusPagamento] = mapped_column(
        Enum(StatusPagamento, native_enum=False, length=20),
        default=StatusPagamento.PENDENTE,
    )
    gatewayTransacaoId: Mapped[str | None] = mapped_column(
        "gateway_transacao_id", String(80), unique=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    payloadResposta: Mapped[dict[str, Any] | None] = mapped_column("payload_resposta", JSON)
    dataHora: Mapped[datetime] = mapped_column(
        "data_hora", DateTime(timezone=True), server_default=func.now()
    )

    def __init__(self, pedidoId: int, metodo: str, valor: Decimal):
        self.pedidoId = pedidoId
        self.metodo = metodo
        self.valor = Decimal(str(valor))
        self.status = StatusPagamento.PENDENTE

    def aprovar(self, transacaoId: str, payload: dict[str, Any]) -> None:
        self.status = StatusPagamento.APROVADO
        self.gatewayTransacaoId = transacaoId
        self.payloadResposta = payload

    def recusar(self, payload: dict[str, Any]) -> None:
        self.status = StatusPagamento.RECUSADO
        self.payloadResposta = payload
