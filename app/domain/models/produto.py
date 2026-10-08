from decimal import Decimal

class Produto():

  def __init__(self, id: int, nome: str, descricao: str, preco: Decimal, categoria: str, ativo: bool):
    self.id: int = id
    self.nome: str = nome
    self.descricao: str = descricao
    self.preco: Decimal = Decimal(str(preco))
    self.categoria: str = categoria
    self.ativo: bool = ativo

  def status_toggle(self):
    self.ativo = not self.ativo

  def __str__(self) -> str:
        status = "Ativo" if self.ativo else "Inativo"
        return f"Produto #{self.id}: {self.nome} - R$ {self.preco:.2f} ({status})"