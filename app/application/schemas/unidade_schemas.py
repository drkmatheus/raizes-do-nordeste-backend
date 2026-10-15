from pydantic import BaseModel, ConfigDict, Field


class UnidadeCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    tipo: str = Field(min_length=1, max_length=30)
    cnpj: str = Field(min_length=14, max_length=18)
    endereco: str | None = Field(default=None, max_length=255)


class UnidadeResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: str
    cnpj: str
    endereco: str | None
