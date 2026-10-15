from sqlalchemy.orm import Session

from app.application.schemas.pedido_schemas import PedidoCriar
from app.application.services.auditoria_service import AuditoriaService
from app.core.errors import AppError
from app.domain.enums import CanalPedido, StatusPedido
from app.domain.models.pedido import Pedido
from app.infrastructure.repositories.estoque_repository import EstoqueRepository
from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.produto_repository import ProdutoRepository
from app.infrastructure.repositories.unidade_repository import UnidadeRepository


class PedidoService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = PedidoRepository(session)
        self.unidades = UnidadeRepository(session)
        self.produtos = ProdutoRepository(session)
        self.estoque = EstoqueRepository(session)
        self.auditoria = AuditoriaService(session)

    def criar(self, dados: PedidoCriar, clienteId: int | None) -> tuple[Pedido, bool]:
        """Retorna ou o pedido novo ou o criado). Se criado=False quando o requestId ja existia
        (idempotencia): devolve o mesmo pedido sem duplicar nem baixar estoque de novo."""
        if dados.requestId:
            existente = self.repo.obterPorRequestId(dados.requestId)
            if existente is not None:
                return existente, False

        if self.unidades.obterPorId(dados.unidadeId) is None:
            raise AppError(404, "UNIDADE_NAO_ENCONTRADA",
                           f"Unidade {dados.unidadeId} nao encontrada.")

        pedido = Pedido(
            canalPedido=dados.canalPedido,
            unidadeId=dados.unidadeId,
            clienteId=clienteId,
            requestId=dados.requestId,
        )

        # Valida produtos/estoque e baixa estoque na mesma transacao.
        estoques_para_baixar: list[tuple] = []
        for item in dados.itens:
            produto = self.produtos.obterPorId(item.produtoId)
            if produto is None:
                raise AppError(404, "PRODUTO_NAO_ENCONTRADO",
                               f"Produto {item.produtoId} nao encontrado.")
            if not produto.ativo:
                raise AppError(409, "PRODUTO_INDISPONIVEL",
                               f"Produto {item.produtoId} esta inativo.")

            estoque = self.estoque.obterParaAtualizar(dados.unidadeId, item.produtoId)
            if estoque is None or not estoque.temSaldo(item.quantidade):
                disponivel = estoque.quantidade if estoque else 0
                raise AppError(
                    409, "ESTOQUE_INSUFICIENTE",
                    "Nao ha quantidade suficiente para um ou mais itens.",
                    [{"field": f"produto {item.produtoId}", "issue": f"Disponivel: {disponivel}"}],
                )
            pedido.adicionarItem(produto, item.quantidade)
            estoques_para_baixar.append((estoque, item.quantidade))

        self.repo.adicionar(pedido)
        for estoque, qtd in estoques_para_baixar:
            estoque.baixar(qtd)

        self.auditoria.registrar(
            "PEDIDO_CRIADO", "pedido", pedido.id, clienteId,
            {"canalPedido": pedido.canalPedido.value, "valorTotal": float(pedido.valorTotal)},
        )
        self.session.commit()
        return pedido, True

    def buscar(self, pedidoId: int) -> Pedido:
        pedido = self.repo.obterPorId(pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        return pedido

    def listar(self, limite: int, deslocamento: int,
               canalPedido: CanalPedido | None = None,
               status: StatusPedido | None = None) -> list[Pedido]:
        return self.repo.listar(limite, deslocamento, canalPedido, status)

    def atualizarStatus(self, pedidoId: int, novo: StatusPedido,
                        usuarioId: int | None = None) -> Pedido:
        pedido = self.repo.obterPorIdParaAtualizar(pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")

        if novo == StatusPedido.CANCELADO:
            return self._cancelar(pedido, usuarioId)

        anterior = pedido.status
        if not pedido.atualizarStatus(novo):
            raise AppError(
                409, "TRANSICAO_INVALIDA",
                f"Nao e possivel mudar de {anterior.value} para {novo.value}.",
            )
        self.auditoria.registrar(
            "STATUS_ALTERADO", "pedido", pedido.id, usuarioId,
            {"de": anterior.value, "para": novo.value},
        )
        self.session.commit()
        return pedido

    def cancelar(self, pedidoId: int, usuarioId: int | None = None) -> Pedido:
        pedido = self.repo.obterPorIdParaAtualizar(pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        return self._cancelar(pedido, usuarioId)

    def _cancelar(self, pedido: Pedido, usuarioId: int | None) -> Pedido:
        anterior = pedido.status
        if not pedido.cancelar():
            raise AppError(
                409, "TRANSICAO_INVALIDA",
                f"Nao e possivel cancelar um pedido em {anterior.value}.",
            )
        # Devolve o estoque reservado pelos itens.
        for item in pedido.itens:
            estoque = self.estoque.obterParaAtualizar(pedido.unidadeId, item.produtoId)
            if estoque is not None:
                estoque.repor(item.quantidade)
        self.auditoria.registrar(
            "PEDIDO_CANCELADO", "pedido", pedido.id, usuarioId,
            {"de": anterior.value},
        )
        self.session.commit()
        return pedido
