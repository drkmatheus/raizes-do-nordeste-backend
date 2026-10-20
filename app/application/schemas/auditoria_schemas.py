from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class LogAuditoriaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuarioId: int | None
    acao: str
    entidade: str
    entidadeId: int | None
    dataHora: datetime
    detalhes: dict[str, Any] | None
