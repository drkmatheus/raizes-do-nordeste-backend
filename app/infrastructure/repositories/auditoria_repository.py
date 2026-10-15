from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.log_auditoria import LogAuditoria


class AuditoriaRepository:
    def __init__(self, session: Session):
        self.session = session

    def listar(self, limite: int = 50, deslocamento: int = 0,
               entidade: str | None = None) -> list[LogAuditoria]:
        stmt = select(LogAuditoria)
        if entidade is not None:
            stmt = stmt.where(LogAuditoria.entidade == entidade)
        stmt = stmt.order_by(LogAuditoria.id.desc()).limit(limite).offset(deslocamento)
        return list(self.session.scalars(stmt))

    def adicionar(self, log: LogAuditoria) -> LogAuditoria:
        self.session.add(log)
        self.session.flush()
        return log
