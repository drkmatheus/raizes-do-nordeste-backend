from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.schemas.usuario_schemas import UsuarioCriar
from app.core.errors import AppError
from app.core.security import hash_senha
from app.domain.enums import Perfil
from app.domain.models.usuario import Usuario
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

class UsuarioService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = UsuarioRepository(session)

    def criar(self, dados: UsuarioCriar) -> Usuario:
        email = dados.email.lower()
        if self.repo.obterPorEmail(email):
            raise self._emailJaCadastrado()

        usuario = Usuario(
            nome=dados.nome,
            email=email,
            senhaHash=hash_senha(dados.senha),
            perfil=Perfil.CLIENTE,
            consentimentoLgpd=dados.consentimentoLgpd,
            consentimentoFidelidade=dados.consentimentoFidelidade,
        )
        try:
            self.repo.adicionar(usuario)
            self.session.commit()
        except IntegrityError:  # evita race condition caso outro request tenha criado o mesmo email
            self.session.rollback()
            raise self._emailJaCadastrado()
        return usuario

    def buscar(self, usuarioId: int) -> Usuario:
        usuario = self.repo.obterPorId(usuarioId)
        if usuario is None:
            raise self._naoEncontrado(usuarioId)
        return usuario

    def listar(self, limite: int, deslocamento: int) -> list[Usuario]:
        return self.repo.listar(limite, deslocamento)

    def anonimizar(self, usuarioId: int) -> None:
        usuario = self.repo.obterPorIdParaAtualizar(usuarioId)
        if usuario is None:
            raise self._naoEncontrado(usuarioId)
        usuario.anonimizar()
        self.session.commit()

    @staticmethod
    def _emailJaCadastrado() -> AppError:
        return AppError(409, "EMAIL_JA_CADASTRADO", "Já existe um usuário com este e-mail.")

    @staticmethod
    def _naoEncontrado(usuarioId: int) -> AppError:
        return AppError(404, "USUARIO_NAO_ENCONTRADO", f"Usuário {usuarioId} não encontrado.")