from sqlalchemy.orm import Session

from app.application.schemas.pedido_schemas import PedidoCriar
from app.application.services.auditoria_service import AuditoriaService
from app.core.errors import AppError
from app.domain.enums import CanalPedido, PERFIS_STAFF, Perfil, StatusPedido
from app.domain.models.pedido import Pedido
from app.domain.models.usuario import Usuario
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

        # Valida produtos/estoque e baixa estoque na mesma transacao
        estoques_para_baixar: list[tuple] = []
        quantidades_por_produto: dict[int, int] = {}
        for item in dados.itens:
            quantidades_por_produto[item.produtoId] = (
                quantidades_por_produto.get(item.produtoId, 0) + item.quantidade
            )

        for produtoId, quantidade in quantidades_por_produto.items():
            produto = self.produtos.obterPorId(produtoId)
            if produto is None:
                raise AppError(404, "PRODUTO_NAO_ENCONTRADO",
                               f"Produto {produtoId} nao encontrado.")
            if not produto.ativo:
                raise AppError(409, "PRODUTO_INDISPONIVEL",
                               f"Produto {produtoId} esta inativo.")

            estoque = self.estoque.obterParaAtualizar(dados.unidadeId, produtoId)
            if estoque is None or not estoque.temSaldo(quantidade):
                disponivel = estoque.quantidade if estoque else 0
                raise AppError(
                    409, "ESTOQUE_INSUFICIENTE",
                    "Nao ha quantidade suficiente para um ou mais itens.",
                    [{"field": f"produto {produtoId}", "issue": f"Disponivel: {disponivel}"}],
                )
            pedido.adicionarItem(produto, quantidade)
            estoques_para_baixar.append((estoque, quantidade))

        self.repo.adicionar(pedido)
        for estoque, qtd in estoques_para_baixar:
            estoque.baixar(qtd)

        self.auditoria.registrar(
            "PEDIDO_CRIADO", "pedido", pedido.id, clienteId,
            {"canalPedido": pedido.canalPedido.value, "valorTotal": float(pedido.valorTotal)},
        )
        self.session.commit()
        return pedido, True

    def buscar(self, pedidoId: int, usuario: Usuario | None = None) -> Pedido:
        pedido = self.repo.obterPorId(pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        # Ownership: CLIENTE so acessa o proprio pedido. Para nao revelar a
        # existencia de pedidos alheios, respondemos 404 (e nao 403)
        if usuario is not None and not self._podeVerTodos(usuario) \
                and pedido.clienteId != usuario.id:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        return pedido

    def listar(self, limite: int, deslocamento: int,
               canalPedido: CanalPedido | None = None,
               status: StatusPedido | None = None,
               usuario: Usuario | None = None) -> list[Pedido]:
        # CLIENTE enxerga apenas os proprios pedidos; staff enxerga todos.
        clienteId = None
        if usuario is not None and not self._podeVerTodos(usuario):
            clienteId = usuario.id
        return self.repo.listar(limite, deslocamento, canalPedido, status, clienteId)

    @staticmethod
    def _podeVerTodos(usuario: Usuario) -> bool:
        return usuario.perfil in PERFIS_STAFF

    @staticmethod
    def _validarUnidade(pedido: Pedido, usuario: Usuario | None) -> None:
        """ GERENTE so opera pedidos da propria unidade; ADMIN e global

        Demais perfis de staff (ATENDENTE/COZINHA) seguem a regra anterior"""
        if usuario is None or usuario.perfil != Perfil.GERENTE:
            return
        if usuario.unidadeId is not None and usuario.unidadeId != pedido.unidadeId:
            raise AppError(
                403, "SEM_PERMISSAO",
                "Gerente so pode operar pedidos da propria unidade.",
            )

    def atualizarStatus(self, pedidoId: int, novo: StatusPedido,
                        usuario: Usuario | None = None) -> Pedido:
        usuarioId = usuario.id if usuario is not None else None
        pedido = self.repo.obterPorIdParaAtualizar(pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        self._validarUnidade(pedido, usuario)

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

    def cancelar(self, pedidoId: int, usuario: Usuario | None = None) -> Pedido:
        usuarioId = usuario.id if usuario is not None else None
        pedido = self.repo.obterPorIdParaAtualizar(pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        self._validarUnidade(pedido, usuario)
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
