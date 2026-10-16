from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_usuario_logado
from app.application.schemas.auth_schemas import LoginRequest, TokenResposta
from app.application.schemas.usuario_schemas import UsuarioResposta
from app.application.services.auth_service import AuthService
from app.domain.models.usuario import Usuario

router = APIRouter()


@router.post("/login", response_model=TokenResposta)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    """ Autentica o usuario e retorna um token JWT"""
    return AuthService(db).login(dados)


@router.get("/me", response_model=UsuarioResposta)
def me(usuario: Usuario = Depends(get_usuario_logado)):
    """ Retorna o perfil do usuario autenticado"""
    return usuario
