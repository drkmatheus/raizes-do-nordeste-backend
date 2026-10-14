"""Importa todas as entidades para registra-las em Base.metadata (migrations)."""
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.domain.models.produto import Produto
from app.domain.models.estoque import Estoque
from app.domain.models.pedido import Pedido
from app.domain.models.item_pedido import ItemPedido
from app.domain.models.pagamento import Pagamento
from app.domain.models.historico_fidelidade import HistoricoFidelidade
from app.domain.models.log_auditoria import LogAuditoria

__all__ = [
    "Unidade",
    "Usuario",
    "Produto",
    "Estoque",
    "Pedido",
    "ItemPedido",
    "Pagamento",
    "HistoricoFidelidade",
    "LogAuditoria",
]
