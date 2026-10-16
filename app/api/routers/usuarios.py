from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfil, get_db
from app.application.schemas.usuario_schemas import UsuarioCriar, UsuarioResposta
from app.application.services.usuario_service import UsuarioService
from app.domain.enums import Perfil

router = APIRouter()


def get_usuario_service(db: Session = Depends(get_db)) -> UsuarioService:
    return UsuarioService(db)


@router.post("", response_model=UsuarioResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: UsuarioCriar, service: UsuarioService = Depends(get_usuario_service)):
    """ Cadastro publico de cliente (perfil CLIENTE)"""
    return service.criar(dados)


@router.get("/{usuario_id}", response_model=UsuarioResposta,
            dependencies=[Depends(exigir_perfil(Perfil.GERENTE, Perfil.ADMIN))])
def obter(usuario_id: int, service: UsuarioService = Depends(get_usuario_service)):
    return service.buscar(usuario_id)


@router.get("", response_model=list[UsuarioResposta],
            dependencies=[Depends(exigir_perfil(Perfil.GERENTE, Perfil.ADMIN))])
def listar(
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: UsuarioService = Depends(get_usuario_service),
):
    return service.listar(limite, deslocamento)


@router.post("/{usuario_id}/anonimizar", status_code=status.HTTP_204_NO_CONTENT,
             dependencies=[Depends(exigir_perfil(Perfil.ADMIN))])
def anonimizar(usuario_id: int, service: UsuarioService = Depends(get_usuario_service)):
    service.anonimizar(usuario_id)
