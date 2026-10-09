# Raizes do Nordeste - API (Trilha Back-End)

Back-end em **Python + FastAPI**, com **SQLAlchemy 2 + Alembic** e **PostgreSQL**.

## Links (preencher antes da entrega)

- Repositorio: `em breve`
- Swagger local: http://localhost:8000/docs
- Colecao /Insomnia: `insomnia/` (arquivo .json neste repositorio)

## Requisitos

- Python 3.11 ou superior
- Docker e Docker Compose (para o PostgreSQL e o pgAdmin)

## Como rodar

```bash
# 1. ambiente virtual e dependencias
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. variaveis de ambiente
cp .env.example .env               # Windows: copy .env.example .env
# gere um JWT_SECRET proprio: python -c "import secrets; print(secrets.token_urlsafe(48))"

# 3. banco (PostgreSQL + pgAdmin)
docker compose up -d

# 4. migrations e seed
alembic upgrade head
python -m app.infrastructure.seed  # quando o seed existir

# 5. iniciar a API
fastapi dev app/main.py            # http://localhost:8000
```

- Swagger/OpenAPI: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (login em `.env`: `PGADMIN_EMAIL` / `PGADMIN_PASSWORD`).
  O servidor "Raizes do Nordeste" ja vem cadastrado; a senha do banco e a `POSTGRES_PASSWORD` do `.env`.
  Se mudar `POSTGRES_USER` ou `POSTGRES_DB`, ajuste tambem `docker/pgadmin/servers.json`
  (e recrie o volume: `docker compose down -v`).

## Testes

```bash
pytest
```

Para a colecao Rest (usei o insomnium fork do insomnia): importar o arquivo de `insomnia/`, rodar a pasta Auth primeiro (guarda o token) e seguir a ordem das pastas.

## Arquitetura (camadas)

| Camada         | Pasta                | Responsabilidade                                      |
| -------------- | -------------------- | ----------------------------------------------------- |
| Domain         | `app/domain`         | Entidades e regras de negocio                         |
| Application    | `app/application`    | Casos de uso (services) e DTOs                        |
| Infrastructure | `app/infrastructure` | Banco, repositorios, gateway de pagamento mock        |
| API            | `app/api`            | Rotas, autenticacao/autorizacao, contratos            |
| Core           | `app/core`           | Configuracao, seguranca (hash e JWT) e padrao de erro |

As entidades de dominio sao mapeadas direto com SQLAlchemy (sem camada extra de mapeamento), para simplificar.

## Documentacao

Diagramas (PlantUML) em `docs/diagramas/`: DER, classes e sequencia.
