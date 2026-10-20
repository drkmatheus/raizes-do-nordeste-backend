from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfil, get_db
from app.api.responses import respostas
from app.application.schemas.estoque_schemas import (
    EstoqueCriar,
    EstoqueResposta,
    MovimentacaoEstoque,
)
from app.application.services.estoque_service import EstoqueService
from app.domain.enums import Perfil
from app.domain.models.usuario import Usuario

router = APIRouter()

_gestor = exigir_perfil(Perfil.GERENTE, Perfil.ADMIN)


def get_service(db: Session = Depends(get_db)) -> EstoqueService:
    return EstoqueService(db)


@router.post("", response_model=EstoqueResposta, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(_gestor)], responses=respostas(401, 403, 404, 409, 422))
def criar(dados: EstoqueCriar, service: EstoqueService = Depends(get_service)):
    """ Cria o registro de estoque de um produto em uma unidade"""
    return service.criar(dados)


@router.get("/unidades/{unidade_id}", response_model=list[EstoqueResposta],
            responses=respostas(404))
def listar_por_unidade(
    unidade_id: int,
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: EstoqueService = Depends(get_service),
):
    """ Consulta o saldo de estoque por unidade"""
    return service.listarPorUnidade(unidade_id, limite, deslocamento)


@router.get("/unidades/{unidade_id}/produtos/{produto_id}", response_model=EstoqueResposta,
            responses=respostas(404))
def consultar_saldo(unidade_id: int, produto_id: int,
                    service: EstoqueService = Depends(get_service)):
    return service.consultarSaldo(unidade_id, produto_id)


@router.post("/unidades/{unidade_id}/produtos/{produto_id}/entradas",
             response_model=EstoqueResposta, responses=respostas(401, 403, 404, 422))
def entrada(unidade_id: int, produto_id: int, dados: MovimentacaoEstoque,
            service: EstoqueService = Depends(get_service),
            usuario: Usuario = Depends(_gestor)):
    """ Entrada de estoque (reposicao)"""
    return service.registrarEntrada(unidade_id, produto_id, dados.quantidade, usuario.id)


@router.post("/unidades/{unidade_id}/produtos/{produto_id}/saidas",
             response_model=EstoqueResposta, responses=respostas(401, 403, 404, 409, 422))
def saida(unidade_id: int, produto_id: int, dados: MovimentacaoEstoque,
          service: EstoqueService = Depends(get_service),
          usuario: Usuario = Depends(_gestor)):
    """ Saida de estoque (baixa manual)"""
    return service.registrarSaida(unidade_id, produto_id, dados.quantidade, usuario.id)
