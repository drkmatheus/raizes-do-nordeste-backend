from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import StatusPagamento


class PagamentoCriar(BaseModel):
    pedidoId: int
    # "MOCK" aprova; "MOCK_FALHA" recusa; "MOCK_TIMEOUT" simula indisponibilidade.
    metodo: str = Field(default="MOCK", max_length=30)


class PagamentoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedidoId: int
    metodo: str
    status: StatusPagamento
    gatewayTransacaoId: str | None
    valor: Decimal
    payloadResposta: dict[str, Any] | None
    dataHora: datetime
