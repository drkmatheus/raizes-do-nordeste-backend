from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import TipoPontos


class ResgatarPontosRequest(BaseModel):
    pontos: int = Field(gt=0)


class SaldoResposta(BaseModel):
    usuarioId: int
    saldoPontos: int
    consentimentoFidelidade: bool


class HistoricoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuarioId: int
    pedidoId: int | None
    tipo: TipoPontos
    pontos: int
    dataHora: datetime
