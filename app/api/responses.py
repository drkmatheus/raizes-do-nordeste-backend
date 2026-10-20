""" Respostas de erro reutilizaveis para o OpenAPI/Swagger

Cada router declara, por operacao, quais status de erro pode devolver usando
`respostas(...)`. Todos apontam para o mesmo modelo ErroResposta, que espelha o
corpo real produzido por app.core.errors. Assim a documentacao bate com a
resposta de runtime sem repetir a estrutura em cada endpoint
"""
from app.application.schemas.erro_schemas import ErroResposta

# Descricoes curtas por status. O FastAPI usa a chave como HTTP status code
_DESCRICOES: dict[int, str] = {
    400: "Requisicao invalida.",
    401: "Token ausente, invalido ou expirado.",
    403: "Usuario autenticado sem permissao para a operacao.",
    404: "Recurso nao encontrado.",
    409: "Conflito com o estado atual do recurso.",
    422: "Dados da requisicao invalidos (falha de validacao).",
    502: "Resposta invalida de um servico externo.",
    503: "Servico externo (ex.: gateway de pagamento) indisponivel.",
}


def respostas(*status_codes: int) -> dict[int | str, dict]:
    """Monta o dict `responses=` do FastAPI para os status informados.

    Uso: `@router.get(..., responses=respostas(401, 404))`.
    """
    return {
        codigo: {
            "model": ErroResposta,
            "description": _DESCRICOES.get(codigo, "Erro."),
        }
        for codigo in status_codes
    }
