from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import CanalPedido, StatusPedido


class ItemPedidoCriar(BaseModel):
    produtoId: int
    quantidade: int = Field(gt=0)


class PedidoCriar(BaseModel):
    # canalPedido obrigatorio (multicanalidade); a ausencia gera 422 no padrão da API
    canalPedido: CanalPedido
    unidadeId: int
    itens: list[ItemPedidoCriar] = Field(min_length=1)
    requestId: str | None = Field(default=None, max_length=80)


class AtualizarStatusRequest(BaseModel):
    status: StatusPedido


class ItemPedidoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produtoId: int
    quantidade: int
    precoUnitario: Decimal


class PedidoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clienteId: int | None
    unidadeId: int
    canalPedido: CanalPedido
    status: StatusPedido
    valorDesconto: Decimal
    valorTotal: Decimal
    requestId: str | None
    dataCriacao: datetime
    itens: list[ItemPedidoResposta]
