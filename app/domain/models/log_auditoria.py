from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class LogAuditoria(Base):
    """ Auditoria de ações sensiveis (foco LGPD e rastreabilidade na API)"""

    __tablename__ = "log_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuarioId: Mapped[int | None] = mapped_column("usuario_id", ForeignKey("usuario.id"), index=True)
    acao: Mapped[str] = mapped_column(String(60))
    entidade: Mapped[str] = mapped_column(String(60))
    entidadeId: Mapped[int | None] = mapped_column("entidade_id")
    dataHora: Mapped[datetime] = mapped_column(
        "data_hora", DateTime(timezone=True), server_default=func.now()
    )
    detalhes: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    def __init__(self, acao: str, entidade: str, entidadeId: int | None = None, usuarioId: int | None = None, detalhes: dict[str, Any] | None = None):
        self.acao = acao
        self.entidade = entidade
        self.entidadeId = entidadeId
        self.usuarioId = usuarioId
        self.detalhes = detalhes
