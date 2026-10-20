""" Schema do corpo de erro padrao da API.

Espelha o formato produzido por app.core.errors (AppError / handlers). Serve
apenas para o Swagger/OpenAPI documentar as respostas de erro com o mesmo
contrato devolvido em runtime
"""
from pydantic import BaseModel, ConfigDict, Field


class ErroDetalhe(BaseModel):
    field: str = Field(description="Campo ou recurso relacionado ao problema.")
    issue: str = Field(description="Descricao do problema encontrado.")


class ErroResposta(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "NAO_ENCONTRADO",
                "message": "Recurso solicitado nao encontrado.",
                "details": [],
                "timestamp": "2026-02-05T12:00:00Z",
                "path": "/pedidos/123",
            }
        }
    )

    error: str = Field(description="Codigo simbolico do erro (ex.: NAO_AUTENTICADO).")
    message: str = Field(description="Mensagem legivel para humanos.")
    details: list[ErroDetalhe] = Field(
        default_factory=list, description="Lista opcional de detalhes por campo."
    )
    timestamp: str = Field(description="Instante do erro em UTC (ISO 8601).")
    path: str = Field(description="Caminho da requisicao que gerou o erro.")
