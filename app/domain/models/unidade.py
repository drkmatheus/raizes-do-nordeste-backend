from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class Unidade(Base):
    __tablename__ = "unidade"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(30))
    endereco: Mapped[str | None] = mapped_column(String(255))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)

    def __init__(self, nome: str, tipo: str, cnpj: str, endereco: str | None = None):
        self.nome = nome
        self.tipo = tipo
        self.cnpj = cnpj
        self.endereco = endereco
