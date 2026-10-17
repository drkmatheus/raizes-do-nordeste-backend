import os
from decimal import Decimal

# Define o ambiente de teste ANTES de importar a aplicacao
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "segredo-de-teste-com-mais-de-32-caracteres"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import hash_senha
from app.domain.base import Base
from app.domain.enums import Perfil
import app.domain.models  # noqa: F401  (registra as entidades)
from app.domain.models.estoque import Estoque
from app.domain.models.produto import Produto
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.main import app


@pytest.fixture
def engine():
    # Banco SQLite em memoria compartilhado entre conexoes do teste
    eng = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Habilita checagem de FOREIGN KEY no SQLite (desligada por padrao)
    @event.listens_for(eng, "connect")
    def _fk_on(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def seed(engine):
    """ Dados minimos: 1 unidade, 1 produto com estoque e usuarios de cada perfil"""
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()

    unidade = Unidade(nome="Matriz", tipo="MATRIZ", cnpj="00.000.000/0001-00")
    session.add(unidade)
    session.flush()

    produto = Produto(nome="Baiao de Dois", preco=Decimal("28.90"), categoria="Prato")
    produto_sem_estoque = Produto(nome="Acaraje", preco=Decimal("18.00"), categoria="Petisco")
    session.add_all([produto, produto_sem_estoque])
    session.flush()

    session.add(Estoque(unidadeId=unidade.id, produtoId=produto.id, quantidade=10))
    session.add(Estoque(unidadeId=unidade.id, produtoId=produto_sem_estoque.id,
                        quantidade=0, disponivel=False))

    usuarios = {
        "cliente": Perfil.CLIENTE,
        "cozinha": Perfil.COZINHA,
        "gerente": Perfil.GERENTE,
        "admin": Perfil.ADMIN,
    }
    criados = {}
    for chave, perfil in usuarios.items():
        u = Usuario(
            nome=chave.title(), email=f"{chave}@teste.com",
            senhaHash=hash_senha("Senha@123"), perfil=perfil,
            consentimentoLgpd=True,
            consentimentoFidelidade=(chave == "cliente"),
        )
        session.add(u)
        session.flush()
        criados[chave] = u.id

    session.commit()
    session.close()

    return {
        "unidadeId": unidade.id,
        "produtoId": produto.id,
        "produtoSemEstoqueId": produto_sem_estoque.id,
        "usuarios": criados,
    }


def _token(client, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "senha": "Senha@123"})
    assert resp.status_code == 200, resp.text
    return resp.json()["accessToken"]


@pytest.fixture
def auth_header(client, seed):
    def _make(perfil: str = "cliente") -> dict:
        return {"Authorization": f"Bearer {_token(client, f'{perfil}@teste.com')}"}

    return _make
