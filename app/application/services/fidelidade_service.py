from sqlalchemy.orm import Session

from app.application.services.auditoria_service import AuditoriaService
from app.core.errors import AppError
from app.domain.enums import TipoPontos
from app.domain.models.historico_fidelidade import HistoricoFidelidade
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.fidelidade_repository import FidelidadeRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class FidelidadeService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = FidelidadeRepository(session)
        self.usuarios = UsuarioRepository(session)
        self.auditoria = AuditoriaService(session)

    def consultarSaldo(self, usuarioId: int) -> Usuario:
        usuario = self.usuarios.obterPorId(usuarioId)
        if usuario is None:
            raise AppError(404, "USUARIO_NAO_ENCONTRADO", f"Usuario {usuarioId} nao encontrado.")
        return usuario

    def resgatar(self, usuarioId: int, pontos: int) -> Usuario:
        usuario = self.usuarios.obterPorIdParaAtualizar(usuarioId)
        if usuario is None:
            raise AppError(404, "USUARIO_NAO_ENCONTRADO", f"Usuario {usuarioId} nao encontrado.")

        # resgatarPontos valida consentimento e saldo, levantando AppError apropriado.
        usuario.resgatarPontos(pontos)
        self.repo.adicionar(
            HistoricoFidelidade(usuarioId=usuario.id, tipo=TipoPontos.RESGATE, pontos=pontos)
        )
        self.auditoria.registrar(
            "PONTOS_RESGATADOS", "usuario", usuario.id, usuarioId,
            {"pontos": pontos, "saldo": usuario.saldoPontos},
        )
        self.session.commit()
        return usuario

    def historico(self, usuarioId: int, limite: int,
                  deslocamento: int) -> list[HistoricoFidelidade]:
        if self.usuarios.obterPorId(usuarioId) is None:
            raise AppError(404, "USUARIO_NAO_ENCONTRADO", f"Usuario {usuarioId} nao encontrado.")
        return self.repo.listarPorUsuario(usuarioId, limite, deslocamento)
