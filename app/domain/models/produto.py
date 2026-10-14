from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class Produto(Base):
    __tablename__ = "produto"
    __table_args__ = (
        CheckConstraint("preco >= 0", name="preco_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(String(255))
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    categoria: Mapped[str | None] = mapped_column(String(60))
    ativo: Mapped[bool] = mapped_column(default=True)

    def __init__(self, nome: str, preco: Decimal, descricao: str | None = None, categoria: str | None = None, ativo: bool = True):
        self.nome = nome
        self.preco = Decimal(str(preco))
        self.descricao = descricao
        self.categoria = categoria
        self.ativo = ativo

    def alternarAtivo(self) -> None:
        self.ativo = not self.ativo
