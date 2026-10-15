from decimal import Decimal

from sqlalchemy.orm import Session

from app.application.schemas.pagamento_schemas import PagamentoCriar
from app.application.services.auditoria_service import AuditoriaService
from app.core.errors import AppError
from app.domain.enums import StatusPedido, TipoPontos
from app.domain.models.historico_fidelidade import HistoricoFidelidade
from app.domain.models.pagamento import Pagamento
from app.infrastructure.gateways.pagamento_mock import (
    GatewayIndisponivelError,
    PagamentoMockGateway,
)
from app.infrastructure.repositories.pagamento_repository import PagamentoRepository
from app.infrastructure.repositories.pedido_repository import PedidoRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

# 1 ponto de fidelidade a cada R$ 1,00 (parte inteira do total).
PONTOS_POR_REAL = 1


class PagamentoService:
    def __init__(self, session: Session, gateway: PagamentoMockGateway | None = None):
        self.session = session
        self.repo = PagamentoRepository(session)
        self.pedidos = PedidoRepository(session)
        self.usuarios = UsuarioRepository(session)
        self.auditoria = AuditoriaService(session)
        self.gateway = gateway or PagamentoMockGateway()

    def solicitar(self, dados: PagamentoCriar, usuarioId: int | None = None) -> Pagamento:
        pedido = self.pedidos.obterPorIdParaAtualizar(dados.pedidoId)
        if pedido is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO",
                           f"Pedido {dados.pedidoId} nao encontrado.")
        if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
            raise AppError(
                409, "PEDIDO_NAO_AGUARDA_PAGAMENTO",
                f"Pedido {pedido.id} esta em {pedido.status.value}, nao aguarda pagamento.",
            )

        pagamento = Pagamento(pedidoId=pedido.id, metodo=dados.metodo, valor=pedido.valorTotal)
        self.repo.adicionar(pagamento)

        try:
            resultado = self.gateway.cobrar(pedido.valorTotal, pedido.id, dados.metodo)
        except GatewayIndisponivelError as exc:
            # Pagamento segue PENDENTE; registra e devolve 503.
            self.auditoria.registrar(
                "PAGAMENTO_INDISPONIVEL", "pagamento", pagamento.id, usuarioId,
                {"pedidoId": pedido.id},
            )
            self.session.commit()
            raise AppError(
                503, "GATEWAY_INDISPONIVEL",
                "Servico de pagamento indisponivel. Tente novamente.",
            ) from exc

        if resultado.aprovado:
            if resultado.transacaoId is None:
                raise AppError(
                    502, "RESPOSTA_GATEWAY_INVALIDA",
                    "Gateway aprovou o pagamento sem informar a transacao.",
                )
            pagamento.aprovar(resultado.transacaoId, resultado.payload)
            pedido.atualizarStatus(StatusPedido.PAGO)
            self._creditarPontos(pedido, usuarioId)
            self.auditoria.registrar(
                "PAGAMENTO_APROVADO", "pagamento", pagamento.id, usuarioId,
                {"pedidoId": pedido.id, "transacaoId": resultado.transacaoId},
            )
        else:
            pagamento.recusar(resultado.payload)
            self.auditoria.registrar(
                "PAGAMENTO_RECUSADO", "pagamento", pagamento.id, usuarioId,
                {"pedidoId": pedido.id},
            )

        self.session.commit()
        return pagamento

    def _creditarPontos(self, pedido, usuarioId: int | None) -> None:
        """ Acumula pontos somente se: houver cliente e consentimento de fidelidade"""
        if pedido.clienteId is None:
            return
        usuario = self.usuarios.obterPorIdParaAtualizar(pedido.clienteId)
        if usuario is None or not usuario.consentimentoFidelidade:
            return
        pontos = int(Decimal(pedido.valorTotal)) * PONTOS_POR_REAL
        if pontos <= 0:
            return
        usuario.acumularPontos(pontos)
        self.session.add(
            HistoricoFidelidade(
                usuarioId=usuario.id, tipo=TipoPontos.GANHO,
                pontos=pontos, pedidoId=pedido.id,
            )
        )

    def listarPorPedido(self, pedidoId: int) -> list[Pagamento]:
        if self.pedidos.obterPorId(pedidoId) is None:
            raise AppError(404, "PEDIDO_NAO_ENCONTRADO", f"Pedido {pedidoId} nao encontrado.")
        return self.repo.listarPorPedido(pedidoId)
