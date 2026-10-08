from enum import Enum

class Perfil(Enum):
  CLIENTE = 1
  ATENDENTE = 2
  COZINHA = 3
  GERENTE = 4
  ADMIN = 5

class CanalPedido(Enum):
  APP = 1
  TOTEM = 2
  BALCAO = 3
  PICKUP = 4
  WEB = 5

class StatusPedido(Enum):
  AGUARDANDO_PAGAMENTO = 1
  PAGO = 2
  EM_PREPARO = 3
  PRONTO = 4
  ENTREGUE = 5 
  CANCELADO = 6

class StatusPagamento(Enum):
  PENDENTE = 1
  APROVADO = 2
  RECUSADO = 3

class TipoPontos(Enum):
  GANHO = 1
  RESGATE = 2
  ESTORNO = 3