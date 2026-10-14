from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base
from app.domain.models.produto import Produto


class Estoque(Base):
    """ Estoque de um produto em uma unidade já que cada unidade tem estoque próprio"""

    __tablename__ = "estoque"
    __table_args__ = (
        UniqueConstraint("unidade_id", "produto_id", name="unidade_produto"),
        CheckConstraint("quantidade >= 0", name="quantidade_nao_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unidadeId: Mapped[int] = mapped_column("unidade_id", ForeignKey("unidade.id"), index=True)
    produtoId: Mapped[int] = mapped_column("produto_id", ForeignKey("produto.id"), index=True)
    quantidade: Mapped[int] = mapped_column(default=0)
    disponivel: Mapped[bool] = mapped_column(default=True)

    produto: Mapped[Produto] = relationship(lazy="joined")

    def __init__(self, unidadeId: int, produtoId: int, quantidade: int = 0,
                 disponivel: bool = True):
        self.unidadeId = unidadeId
        self.produtoId = produtoId
        self.quantidade = quantidade
        self.disponivel = disponivel

    def temSaldo(self, qtd: int) -> bool:
        return self.disponivel and qtd > 0 and self.quantidade >= qtd

    def baixar(self, qtd: int) -> bool:
        if not self.temSaldo(qtd):
            return False
        self.quantidade -= qtd
        if self.quantidade == 0:
            self.disponivel = False
        return True

    def repor(self, qtd: int) -> bool:
        if qtd <= 0:
            return False
        self.quantidade += qtd
        self.disponivel = True
        return True
