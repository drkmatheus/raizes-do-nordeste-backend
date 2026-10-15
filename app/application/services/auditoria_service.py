from typing import Any

from sqlalchemy.orm import Session

from app.domain.models.log_auditoria import LogAuditoria
from app.infrastructure.repositories.auditoria_repository import AuditoriaRepository


class AuditoriaService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = AuditoriaRepository(session)

    def registrar(self, acao: str, entidade: str, entidadeId: int | None = None, usuarioId: int | None = None, detalhes: dict[str, Any] | None = None) -> None:
        self.repo.adicionar(
            LogAuditoria(
                acao=acao,
                entidade=entidade,
                entidadeId=entidadeId,
                usuarioId=usuarioId,
                detalhes=detalhes,
            )
        )

    def listar(self, limite: int, deslocamento: int,
               entidade: str | None = None) -> list[LogAuditoria]:
        return self.repo.listar(limite, deslocamento, entidade)
