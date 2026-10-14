from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.base import Base


class ItemPedido(Base):
    __tablename__ = "item_pedido"
    __table_args__ = (
        UniqueConstraint("pedido_id", "produto_id", name="pedido_produto"),
        CheckConstraint("quantidade > 0", name="quantidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    pedidoId: Mapped[int] = mapped_column("pedido_id", ForeignKey("pedido.id"), index=True)
    produtoId: Mapped[int] = mapped_column("produto_id", ForeignKey("produto.id"))
    quantidade: Mapped[int]
    precoUnitario: Mapped[Decimal] = mapped_column("preco_unitario", Numeric(10, 2))

    def __init__(self, produtoId: int, quantidade: int, precoUnitario: Decimal, pedidoId: int | None = None):
        self.produtoId = produtoId
        self.quantidade = quantidade
        self.precoUnitario = Decimal(str(precoUnitario))
        if pedidoId is not None:
            self.pedidoId = pedidoId

    def subtotal(self) -> Decimal:
        return self.precoUnitario * self.quantidade
