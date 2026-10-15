from pydantic import BaseModel, EmailStr, Field

from app.application.schemas.usuario_schemas import UsuarioResposta


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)


class TokenResposta(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int
    user: UsuarioResposta
