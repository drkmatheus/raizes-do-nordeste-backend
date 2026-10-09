"""Dependencias do FastAPI (equivalente a injecao de dependencia do Spring)."""
from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.infrastructure.database import SessionLocal


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO: get_usuario_logado (le o JWT) e exigir_perfil("GERENTE", ...) -> 401 / 403
