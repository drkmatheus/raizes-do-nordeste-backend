from sqlalchemy.orm import Session

from app.application.schemas.auth_schemas import LoginRequest, TokenResposta
from app.application.schemas.usuario_schemas import UsuarioResposta
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import criar_access_token, verificar_senha
from app.infrastructure.repositories.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = UsuarioRepository(session)

    def login(self, dados: LoginRequest) -> TokenResposta:
        usuario = self.repo.obterPorEmail(dados.email.lower())
        # Mesma resposta para email inexistente ou senha errada (nao vaza qual falhou).
        if usuario is None or not verificar_senha(dados.senha, usuario.senhaHash):
            raise AppError(401, "CREDENCIAIS_INVALIDAS", "E-mail ou senha invalidos.")

        token = criar_access_token(usuario.id, usuario.perfil.value)
        return TokenResposta(
            accessToken=token,
            expiresIn=get_settings().jwt_expire_minutes * 60,
            user=UsuarioResposta.model_validate(usuario),
        )
