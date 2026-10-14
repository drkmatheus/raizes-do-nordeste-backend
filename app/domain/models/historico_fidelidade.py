from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base
from app.domain.enums import TipoPontos


class HistoricoFidelidade(Base):
    __tablename__ = "historico_fidelidade"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuarioId: Mapped[int] = mapped_column("usuario_id", ForeignKey("usuario.id"), index=True)
    pedidoId: Mapped[int | None] = mapped_column("pedido_id", ForeignKey("pedido.id"))
    tipo: Mapped[TipoPontos] = mapped_column(Enum(TipoPontos, native_enum=False, length=20))
    pontos: Mapped[int]
    dataHora: Mapped[datetime] = mapped_column(
        "data_hora", DateTime(timezone=True), server_default=func.now()
    )

    def __init__(self, usuarioId: int, tipo: TipoPontos, pontos: int, pedidoId: int | None = None):
        self.usuarioId = usuarioId
        self.tipo = tipo
        self.pontos = pontos
        self.pedidoId = pedidoId
