from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.base import Base
from app.domain.enums import CanalPedido, StatusPedido
from app.domain.models.item_pedido import ItemPedido
from app.domain.models.produto import Produto


class Pedido(Base):
    __tablename__ = "pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    clienteId: Mapped[int | None] = mapped_column("cliente_id", ForeignKey("usuario.id"), index=True)
    unidadeId: Mapped[int] = mapped_column("unidade_id", ForeignKey("unidade.id"), index=True)
    canalPedido: Mapped[CanalPedido] = mapped_column(
        "canal_pedido", Enum(CanalPedido, native_enum=False, length=20), index=True
    )
    status: Mapped[StatusPedido] = mapped_column(
        Enum(StatusPedido, native_enum=False, length=30),
        default=StatusPedido.AGUARDANDO_PAGAMENTO,
        index=True,
    )
    valorDesconto: Mapped[Decimal] = mapped_column("valor_desconto", Numeric(10, 2), default=0)
    valorTotal: Mapped[Decimal] = mapped_column("valor_total", Numeric(10, 2), default=0)
    requestId: Mapped[str | None] = mapped_column("request_id", String(80), unique=True)
    dataCriacao: Mapped[datetime] = mapped_column(
        "data_criacao", DateTime(timezone=True), server_default=func.now()
    )
    dataAtualizacao: Mapped[datetime] = mapped_column(
        "data_atualizacao", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    itens: Mapped[list[ItemPedido]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    def __init__(self, canalPedido: CanalPedido, unidadeId: int, clienteId: int | None = None, requestId: str | None = None):
        self.canalPedido = canalPedido
        self.unidadeId = unidadeId
        self.clienteId = clienteId
        self.requestId = requestId
        self.status = StatusPedido.AGUARDANDO_PAGAMENTO
        self.valorDesconto = Decimal("0")
        self.valorTotal = Decimal("0")

    def _subtotalBruto(self) -> Decimal:
        return sum((item.subtotal() for item in self.itens), Decimal("0"))

    def adicionarItem(self, produto: Produto, quantidade: int) -> bool:
        if self.status != StatusPedido.AGUARDANDO_PAGAMENTO:
            return False
        if quantidade <= 0 or not produto.ativo:
            return False

        for item in self.itens:
            if item.produtoId == produto.id:
                item.quantidade += quantidade
                break
        else:
            self.itens.append(ItemPedido(produto.id, quantidade, produto.preco))

        self.calcularTotal()
        return True

    def calcularTotal(self) -> Decimal:
        total = self._subtotalBruto() - self.valorDesconto
        self.valorTotal = max(total, Decimal("0"))
        return self.valorTotal

    def aplicarDesconto(self, valor: Decimal) -> bool:
        if self.status != StatusPedido.AGUARDANDO_PAGAMENTO:
            return False
        if valor < 0 or valor > self._subtotalBruto():
            return False
        self.valorDesconto = valor
        self.calcularTotal()
        return True

    def podeTransitarPara(self, novo: StatusPedido) -> bool:
        return self.status.podeTransitarPara(novo)

    def atualizarStatus(self, novo: StatusPedido) -> bool:
        if not self.podeTransitarPara(novo):
            return False
        self.status = novo
        return True

    def cancelar(self) -> bool:
        return self.atualizarStatus(StatusPedido.CANCELADO)
