from sqlalchemy.orm import Session

from app.application.schemas.produto_schemas import ProdutoAtualizar, ProdutoCriar
from app.core.errors import AppError
from app.domain.models.produto import Produto
from app.infrastructure.repositories.produto_repository import ProdutoRepository


class ProdutoService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = ProdutoRepository(session)

    def criar(self, dados: ProdutoCriar) -> Produto:
        produto = Produto(
            nome=dados.nome,
            preco=dados.preco,
            descricao=dados.descricao,
            categoria=dados.categoria,
            ativo=dados.ativo,
        )
        self.repo.adicionar(produto)
        self.session.commit()
        return produto

    def buscar(self, produtoId: int) -> Produto:
        produto = self.repo.obterPorId(produtoId)
        if produto is None:
            raise AppError(404, "PRODUTO_NAO_ENCONTRADO", f"Produto {produtoId} nao encontrado.")
        return produto

    def listar(self, limite: int, deslocamento: int,
               apenasAtivos: bool = False) -> list[Produto]:
        return self.repo.listar(limite, deslocamento, apenasAtivos)

    def atualizar(self, produtoId: int, dados: ProdutoAtualizar) -> Produto:
        produto = self.buscar(produtoId)
        campos = dados.model_dump(exclude_unset=True)
        for campo, valor in campos.items():
            setattr(produto, campo, valor)
        self.session.commit()
        return produto
