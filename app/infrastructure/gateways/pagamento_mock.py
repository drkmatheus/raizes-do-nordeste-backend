import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


class GatewayIndisponivelError(Exception):
    """Falha de comunicacao com o gateway (simula timeout/indisponibilidade)."""


class ResultadoPagamento:
    def __init__(self, aprovado: bool, transacaoId: str | None, payload: dict[str, Any]):
        self.aprovado = aprovado
        self.transacaoId = transacaoId
        self.payload = payload


class PagamentoMockGateway:
    def cobrar(self, valor: Decimal, pedidoId: int, metodo: str) -> ResultadoPagamento:
        agora = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        metodo = (metodo or "").upper()

        if metodo == "MOCK_TIMEOUT":
            raise GatewayIndisponivelError("Gateway de pagamento indisponivel.")

        if metodo == "MOCK_FALHA":
            return ResultadoPagamento(
                aprovado=False,
                transacaoId=None,
                payload={
                    "status": "RECUSADO",
                    "motivo": "Pagamento recusado pelo emissor (mock).",
                    "pedidoId": pedidoId,
                    "valor": float(valor),
                    "processadoEm": agora,
                },
            )

        transacaoId = f"mock_{uuid.uuid4().hex[:16]}"
        return ResultadoPagamento(
            aprovado=True,
            transacaoId=transacaoId,
            payload={
                "status": "APROVADO",
                "transacaoId": transacaoId,
                "pedidoId": pedidoId,
                "valor": float(valor),
                "processadoEm": agora,
            },
        )
