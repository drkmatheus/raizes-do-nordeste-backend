from pydantic import BaseModel, ConfigDict, Field


class EstoqueCriar(BaseModel):
    unidadeId: int
    produtoId: int
    quantidade: int = Field(ge=0, default=0)


class MovimentacaoEstoque(BaseModel):
    quantidade: int = Field(gt=0)


class EstoqueResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unidadeId: int
    produtoId: int
    quantidade: int
    disponivel: bool
