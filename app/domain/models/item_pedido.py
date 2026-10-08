from decimal import Decimal

class ItemPedido:
  def __init__(self, id: int, quantidade: int, precoUnitario: Decimal):
    self.id: int = id
    self.quantidade: int = quantidade
    self.precoUnitario: Decimal = precoUnitario

  def subtotal(self):
    return self.quantidade * self.precoUnitario
