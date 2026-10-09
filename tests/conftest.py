import os

# Define o ambiente de teste ANTES de importar a aplicacao.
# Troque por um Postgres de teste quando os testes passarem a tocar o banco.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "segredo-de-teste-com-mais-de-32-caracteres"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
