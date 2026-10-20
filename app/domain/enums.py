from enum import Enum

class Perfil(str, Enum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"

# Perfis de staff. Usado para distinguir acesso de CLIENTE x equipe:
# CLIENTE so enxerga os proprios recursos; staff enxerga todos
PERFIS_STAFF = frozenset({
    Perfil.ATENDENTE, Perfil.COZINHA, Perfil.GERENTE, Perfil.ADMIN,
})

class CanalPedido(str, Enum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"


class StatusPedido(str, Enum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    PAGO = "PAGO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

    def podeTransitarPara(self, novo: "StatusPedido") -> bool:
        return novo in _TRANSICOES[self]


# Estados do pedido (cozinha -> pronto -> entregue ou cancelado)
_TRANSICOES: dict[StatusPedido, set[StatusPedido]] = {
    StatusPedido.AGUARDANDO_PAGAMENTO: {StatusPedido.PAGO, StatusPedido.CANCELADO},
    StatusPedido.PAGO: {StatusPedido.EM_PREPARO, StatusPedido.CANCELADO},
    StatusPedido.EM_PREPARO: {StatusPedido.PRONTO, StatusPedido.CANCELADO},
    StatusPedido.PRONTO: {StatusPedido.ENTREGUE},
    StatusPedido.ENTREGUE: set(),
    StatusPedido.CANCELADO: set(),
}


class StatusPagamento(str, Enum):
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"


class TipoPontos(str, Enum):
    GANHO = "GANHO"
    RESGATE = "RESGATE"
    ESTORNO = "ESTORNO"
