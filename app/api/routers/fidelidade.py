from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db, get_usuario_logado
from app.application.schemas.fidelidade_schemas import (
    HistoricoResposta,
    ResgatarPontosRequest,
    SaldoResposta,
)
from app.application.services.fidelidade_service import FidelidadeService
from app.domain.models.usuario import Usuario
from sqlalchemy.orm import Session

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> FidelidadeService:
    return FidelidadeService(db)


@router.get("/saldo", response_model=SaldoResposta)
def saldo(service: FidelidadeService = Depends(get_service),
          usuario: Usuario = Depends(get_usuario_logado)):
    """ Saldo de pontos do usuario autenticado"""
    u = service.consultarSaldo(usuario.id)
    return SaldoResposta(
        usuarioId=u.id, saldoPontos=u.saldoPontos,
        consentimentoFidelidade=u.consentimentoFidelidade,
    )


@router.post("/resgates", response_model=SaldoResposta)
def resgatar(dados: ResgatarPontosRequest, service: FidelidadeService = Depends(get_service),
             usuario: Usuario = Depends(get_usuario_logado)):
    """ Resgata pontos do usuario autenticado (exige consentimento e saldo)"""
    u = service.resgatar(usuario.id, dados.pontos)
    return SaldoResposta(
        usuarioId=u.id, saldoPontos=u.saldoPontos,
        consentimentoFidelidade=u.consentimentoFidelidade,
    )


@router.get("/historico", response_model=list[HistoricoResposta])
def historico(
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: FidelidadeService = Depends(get_service),
    usuario: Usuario = Depends(get_usuario_logado),
):
    """ Historico de movimentacoes de pontos do usuario autenticado"""
    return service.historico(usuario.id, limite, deslocamento)
