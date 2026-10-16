from collections.abc import Callable, Iterator

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decodificar_token
from app.domain.enums import Perfil
from app.domain.models.usuario import Usuario
from app.infrastructure.database import SessionLocal

# auto_error=False: devolvemos nosso erro padronizado (401) em vez do default do FastAPI.
_bearer = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_usuario_logado(
    credenciais: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    if credenciais is None or not credenciais.credentials:
        raise AppError(401, "NAO_AUTENTICADO", "Token de autenticacao ausente.")
    try:
        payload = decodificar_token(credenciais.credentials)
    except jwt.InvalidTokenError:
        raise AppError(401, "TOKEN_INVALIDO", "Token invalido ou expirado.")

    usuario_id = payload.get("sub")
    usuario = db.get(Usuario, int(usuario_id)) if usuario_id else None
    if usuario is None:
        raise AppError(401, "NAO_AUTENTICADO", "Usuario do token nao existe mais.")
    return usuario


def exigir_perfil(*perfis: Perfil) -> Callable[[Usuario], Usuario]:
    """ Gera uma dependencia que exige que o usuario logado tenha um dos perfis."""

    def _verificar(usuario: Usuario = Depends(get_usuario_logado)) -> Usuario:
        if usuario.perfil not in perfis:
            permitidos = ", ".join(p.value for p in perfis)
            raise AppError(
                403, "SEM_PERMISSAO",
                f"Acesso restrito aos perfis: {permitidos}.",
            )
        return usuario

    return _verificar
