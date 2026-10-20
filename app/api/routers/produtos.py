from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfil, get_db
from app.api.responses import respostas
from app.application.schemas.produto_schemas import (
    ProdutoAtualizar,
    ProdutoCriar,
    ProdutoResposta,
)
from app.application.services.produto_service import ProdutoService
from app.domain.enums import Perfil

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> ProdutoService:
    return ProdutoService(db)


@router.post("", response_model=ProdutoResposta, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(exigir_perfil(Perfil.GERENTE, Perfil.ADMIN))],
             responses=respostas(401, 403, 422))
def criar(dados: ProdutoCriar, service: ProdutoService = Depends(get_service)):
    return service.criar(dados)


@router.get("", response_model=list[ProdutoResposta])
def listar(
    apenasAtivos: bool = Query(False, description="Lista apenas produtos ativos"),
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: ProdutoService = Depends(get_service),
):
    """ Consulta publica do cardapio"""
    return service.listar(limite, deslocamento, apenasAtivos)


@router.get("/{produto_id}", response_model=ProdutoResposta, responses=respostas(404))
def obter(produto_id: int, service: ProdutoService = Depends(get_service)):
    return service.buscar(produto_id)


@router.patch("/{produto_id}", response_model=ProdutoResposta,
              dependencies=[Depends(exigir_perfil(Perfil.GERENTE, Perfil.ADMIN))],
              responses=respostas(401, 403, 404, 422))
def atualizar(produto_id: int, dados: ProdutoAtualizar,
              service: ProdutoService = Depends(get_service)):
    return service.atualizar(produto_id, dados)
