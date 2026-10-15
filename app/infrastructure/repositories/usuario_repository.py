from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, session: Session):
        self.session = session

    def obterPorId(self, usuarioId: int) -> Usuario | None:
        return self.session.get(Usuario, usuarioId)

    def obterPorIdParaAtualizar(self, usuarioId: int) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.id == usuarioId).with_for_update()
        return self.session.scalars(stmt).one_or_none()

    def obterPorEmail(self, email: str) -> Usuario | None:
        stmt = select(Usuario).where(Usuario.email == email)
        return self.session.scalars(stmt).one_or_none()

    def listar(self, limite: int = 50, deslocamento: int = 0) -> list[Usuario]:
        stmt = select(Usuario).order_by(Usuario.id).limit(limite).offset(deslocamento)
        return list(self.session.scalars(stmt))

    def adicionar(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.flush()
        return usuario
