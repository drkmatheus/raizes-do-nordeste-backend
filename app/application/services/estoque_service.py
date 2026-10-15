from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.schemas.estoque_schemas import EstoqueCriar
from app.application.services.auditoria_service import AuditoriaService
from app.core.errors import AppError
from app.domain.models.estoque import Estoque
from app.infrastructure.repositories.estoque_repository import EstoqueRepository
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.repositories.unidade_repository import UnidadeRepository


class EstoqueService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = EstoqueRepository(session)
        self.produtos = ProdutoRepository(session)
        self.unidades = UnidadeRepository(session)
        self.auditoria = AuditoriaService(session)

    def criar(self, dados: EstoqueCriar) -> Estoque:
        if self.unidades.obterPorId(dados.unidadeId) is None:
            raise AppError(404, "UNIDADE_NAO_ENCONTRADA",
                           f"Unidade {dados.unidadeId} nao encontrada.")
        if self.produtos.obterPorId(dados.produtoId) is None:
            raise AppError(404, "PRODUTO_NAO_ENCONTRADO",
                           f"Produto {dados.produtoId} nao encontrado.")

        estoque = Estoque(
            unidadeId=dados.unidadeId,
            produtoId=dados.produtoId,
            quantidade=dados.quantidade,
            disponivel=dados.quantidade > 0,
        )
        try:
            self.repo.adicionar(estoque)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise AppError(409, "ESTOQUE_JA_EXISTE",
                           "Ja existe estoque deste produto nesta unidade.")
        return estoque

    def listarPorUnidade(self, unidadeId: int, limite: int,
                         deslocamento: int) -> list[Estoque]:
        if self.unidades.obterPorId(unidadeId) is None:
            raise AppError(404, "UNIDADE_NAO_ENCONTRADA",
                           f"Unidade {unidadeId} nao encontrada.")
        return self.repo.listarPorUnidade(unidadeId, limite, deslocamento)

    def consultarSaldo(self, unidadeId: int, produtoId: int) -> Estoque:
        estoque = self.repo.obter(unidadeId, produtoId)
        if estoque is None:
            raise AppError(404, "ESTOQUE_NAO_ENCONTRADO",
                           "Nao ha estoque deste produto nesta unidade.")
        return estoque

    def registrarEntrada(self, unidadeId: int, produtoId: int, quantidade: int,
                         usuarioId: int | None = None) -> Estoque:
        estoque = self.repo.obterParaAtualizar(unidadeId, produtoId)
        if estoque is None:
            raise AppError(404, "ESTOQUE_NAO_ENCONTRADO",
                           "Nao ha estoque deste produto nesta unidade.")
        estoque.repor(quantidade)
        self.auditoria.registrar(
            "ESTOQUE_ENTRADA", "estoque", estoque.id, usuarioId,
            {"quantidade": quantidade, "saldo": estoque.quantidade},
        )
        self.session.commit()
        return estoque

    def registrarSaida(self, unidadeId: int, produtoId: int, quantidade: int,
                       usuarioId: int | None = None) -> Estoque:
        estoque = self.repo.obterParaAtualizar(unidadeId, produtoId)
        if estoque is None:
            raise AppError(404, "ESTOQUE_NAO_ENCONTRADO",
                           "Nao ha estoque deste produto nesta unidade.")
        if not estoque.baixar(quantidade):
            raise AppError(
                409, "ESTOQUE_INSUFICIENTE",
                "Nao ha quantidade suficiente para a saida.",
                [{"field": "quantidade", "issue": f"Disponivel: {estoque.quantidade}"}],
            )
        self.auditoria.registrar(
            "ESTOQUE_SAIDA", "estoque", estoque.id, usuarioId,
            {"quantidade": quantidade, "saldo": estoque.quantidade},
        )
        self.session.commit()
        return estoque
