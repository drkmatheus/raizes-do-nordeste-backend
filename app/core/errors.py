"""Padrao unico de erro da API

Toda falha devolve:
{
  "error": "NOME_DO_ERRO",
  "message": "Mensagem legivel",
  "details": [{"field": "campo", "issue": "problema"}],
  "timestamp": "2026-02-05T12:00:00Z",
  "path": "/rota"
}
"""
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

NOMES_POR_STATUS = {
    400: "REQUISICAO_INVALIDA",
    401: "NAO_AUTENTICADO",
    403: "SEM_PERMISSAO",
    404: "NAO_ENCONTRADO",
    405: "METODO_NAO_PERMITIDO",
    409: "CONFLITO",
    422: "DADOS_INVALIDOS",
}


class AppError(Exception):
    """Erro de negocio. Levante nos services, ex.: AppError(409, "ESTOQUE_INSUFICIENTE", "...")."""

    def __init__(self, status_code: int, error: str, message: str, details: list[dict] | None = None):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.details = details or []
        super().__init__(message)


def _resposta(request: Request, status_code: int, error: str, message: str, details: list[dict] | None = None):
    corpo = {
        "error": error,
        "message": message,
        "details": details or [],
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "path": request.url.path,
    }
    return JSONResponse(status_code=status_code, content=corpo)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def tratar_app_error(request: Request, exc: AppError):
        return _resposta(request, exc.status_code, exc.error, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def tratar_validacao(request: Request, exc: RequestValidationError):
        detalhes = [
            {"field": ".".join(str(p) for p in erro["loc"][1:]), "issue": erro["msg"]}
            for erro in exc.errors()
        ]
        return _resposta(request, 422, "DADOS_INVALIDOS", "Dados da requisicao invalidos.", detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def tratar_http(request: Request, exc: StarletteHTTPException):
        nome = NOMES_POR_STATUS.get(exc.status_code, "ERRO_HTTP")
        mensagem = exc.detail if isinstance(exc.detail, str) else "Erro na requisicao."
        return _resposta(request, exc.status_code, nome, mensagem)

    @app.exception_handler(Exception)
    async def tratar_inesperado(request: Request, exc: Exception):
        return _resposta(request, 500, "ERRO_INTERNO", "Erro interno do servidor.")
