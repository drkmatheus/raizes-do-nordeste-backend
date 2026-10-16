from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfil, get_db
from app.application.schemas.unidade_schemas import UnidadeCriar, UnidadeResposta
from app.application.services.unidade_service import UnidadeService
from app.domain.enums import Perfil

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> UnidadeService:
    return UnidadeService(db)


@router.post("", response_model=UnidadeResposta, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(exigir_perfil(Perfil.ADMIN))])
def criar(dados: UnidadeCriar, service: UnidadeService = Depends(get_service)):
    return service.criar(dados)


@router.get("", response_model=list[UnidadeResposta])
def listar(
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: UnidadeService = Depends(get_service),
):
    """ Lista publica das unidades da rede"""
    return service.listar(limite, deslocamento)


@router.get("/{unidade_id}", response_model=UnidadeResposta)
def obter(unidade_id: int, service: UnidadeService = Depends(get_service)):
    return service.buscar(unidade_id)
