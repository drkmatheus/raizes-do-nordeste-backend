from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_usuario_logado
from app.api.responses import respostas
from app.application.schemas.pagamento_schemas import PagamentoCriar, PagamentoResposta
from app.application.services.pagamento_service import PagamentoService
from app.domain.models.usuario import Usuario

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> PagamentoService:
    return PagamentoService(db)


@router.post("", response_model=PagamentoResposta,
             responses=respostas(401, 404, 409, 502, 503))
def solicitar(dados: PagamentoCriar, service: PagamentoService = Depends(get_service),
              usuario: Usuario = Depends(get_usuario_logado)):
    """ Solicita o pagamento (mock) de um pedido e devolve status + payload do gateway.

    CLIENTE so paga o proprio pedido; equipe (staff) pode pagar qualquer um.
    metodo: "MOCK" aprova, "MOCK_FALHA" recusa, "MOCK_TIMEOUT" simula indisponibilidade (503)"""
    return service.solicitar(dados, usuario)


@router.get("/pedidos/{pedido_id}", response_model=list[PagamentoResposta],
            responses=respostas(401, 404))
def listar_por_pedido(pedido_id: int, service: PagamentoService = Depends(get_service),
                      usuario: Usuario = Depends(get_usuario_logado)):
    """ Historico de tentativas de pagamento de um pedido. CLIENTE so ve o proprio."""
    return service.listarPorPedido(pedido_id, usuario)
