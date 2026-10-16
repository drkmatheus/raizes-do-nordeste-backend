from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfil, get_db, get_usuario_logado
from app.application.schemas.pedido_schemas import (
    AtualizarStatusRequest,
    PedidoCriar,
    PedidoResposta,
)
from app.application.services.pedido_service import PedidoService
from app.domain.enums import CanalPedido, Perfil, StatusPedido
from app.domain.models.usuario import Usuario

router = APIRouter()

_operacao = exigir_perfil(Perfil.COZINHA, Perfil.ATENDENTE, Perfil.GERENTE, Perfil.ADMIN)


def get_service(db: Session = Depends(get_db)) -> PedidoService:
    return PedidoService(db)


@router.post("", response_model=PedidoResposta, status_code=status.HTTP_201_CREATED)
def criar(dados: PedidoCriar, response: Response,
          service: PedidoService = Depends(get_service),
          usuario: Usuario = Depends(get_usuario_logado)):
    """ Cria um pedido validando itens/estoque. Exige canalPedido (multicanalidade)

    Se o mesmo requestId ja foi usado, devolve 200 com o pedido existente (idempotencia/evitar race condition)"""
    pedido, criado = service.criar(dados, usuario.id)
    if not criado:
        response.status_code = status.HTTP_200_OK
    return pedido


@router.get("", response_model=list[PedidoResposta])
def listar(
    canalPedido: CanalPedido | None = Query(None, description="Filtra por canal de origem"),
    status_: StatusPedido | None = Query(None, alias="status"),
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: PedidoService = Depends(get_service),
    _usuario: Usuario = Depends(get_usuario_logado),
):
    """ Lista pedidos, com filtro por canal (?canalPedido=TOTEM) e status"""
    return service.listar(limite, deslocamento, canalPedido, status_)


@router.get("/{pedido_id}", response_model=PedidoResposta)
def obter(pedido_id: int, service: PedidoService = Depends(get_service),
          _usuario: Usuario = Depends(get_usuario_logado)):
    return service.buscar(pedido_id)


@router.patch("/{pedido_id}/status", response_model=PedidoResposta)
def atualizar_status(pedido_id: int, dados: AtualizarStatusRequest,
                     service: PedidoService = Depends(get_service),
                     usuario: Usuario = Depends(_operacao)):
    """ Atualiza o status do pedido (cozinha -> pronto -> entregue / cancelado)"""
    return service.atualizarStatus(pedido_id, dados.status, usuario.id)


@router.post("/{pedido_id}/cancelar", response_model=PedidoResposta)
def cancelar(pedido_id: int, service: PedidoService = Depends(get_service),
             usuario: Usuario = Depends(_operacao)):
    """ Cancela o pedido e devolve o estoque reservado"""
    return service.cancelar(pedido_id, usuario.id)
