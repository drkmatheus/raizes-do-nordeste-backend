from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.domain.enums import Perfil


class UsuarioCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    consentimentoLgpd: bool = False
    consentimentoFidelidade: bool = False


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    perfil: Perfil
    saldoPontos: int
    consentimentoFidelidade: bool

    @field_serializer("perfil")
    def _serializarPerfil(self, perfil: Perfil) -> str:
        return perfil.value
