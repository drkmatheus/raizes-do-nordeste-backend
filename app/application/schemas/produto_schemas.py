from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProdutoCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    preco: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    descricao: str | None = Field(default=None, max_length=255)
    categoria: str | None = Field(default=None, max_length=60)
    ativo: bool = True


class ProdutoAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=120)
    preco: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    descricao: str | None = Field(default=None, max_length=255)
    categoria: str | None = Field(default=None, max_length=60)
    ativo: bool | None = None


class ProdutoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    preco: Decimal
    categoria: str | None
    ativo: bool
