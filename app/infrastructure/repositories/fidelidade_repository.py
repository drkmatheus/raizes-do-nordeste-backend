from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.historico_fidelidade import HistoricoFidelidade


class FidelidadeRepository:
    def __init__(self, session: Session):
        self.session = session

    def listarPorUsuario(self, usuarioId: int, limite: int = 50,
                         deslocamento: int = 0) -> list[HistoricoFidelidade]:
        stmt = (
            select(HistoricoFidelidade)
            .where(HistoricoFidelidade.usuarioId == usuarioId)
            .order_by(HistoricoFidelidade.id.desc())
            .limit(limite)
            .offset(deslocamento)
        )
        return list(self.session.scalars(stmt))

    def adicionar(self, historico: HistoricoFidelidade) -> HistoricoFidelidade:
        self.session.add(historico)
        self.session.flush()
        return historico
