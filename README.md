# Raizes do Nordeste - API (Trilha Back-End)

Back-end da rede de restaurantes **Raizes do Nordeste** (matriz + unidades/franquias).
Implementa o fluxo critico **Pedido -> Pagamento mock -> Atualizacao de status**, com
multicanalidade, controle de estoque por unidade, programa de fidelidade, autenticacao
JWT por perfis e auditoria de acoes sensiveis (LGPD).

Stack: **Python 3.11+ / FastAPI**, **SQLAlchemy 2 + Alembic**, **PostgreSQL** (via Docker).

## Links

- Repositorio: `https://github.com/drkmatheus/raizes-do-nordeste-backend`
- Swagger local: http://localhost:8000/docs (rota do Swagger: `/docs`; OpenAPI JSON: `/openapi.json`)
- Colecao Insomnia/Insomnium: `insomnia/raizes_do_nordeste_insomnia.json`

## Requisitos

- Python 3.11 ou superior (testado em 3.12)
- Docker e Docker Compose (para o PostgreSQL e o pgAdmin)
- Dependencias Python em `requirements.txt` (FastAPI, SQLAlchemy, Alembic, psycopg, PyJWT, bcrypt, pytest)

## Como rodar

```bash
# 1. ambiente virtual e dependencias
python -m venv .venv
source .venv/bin/activate          # Windows (bash): source .venv/Scripts/activate
pip install -r requirements.txt

# 2. variaveis de ambiente
cp .env.example .env               # Windows: copy .env.example .env
# gere um JWT_SECRET proprio:
python -c "import secrets; print(secrets.token_urlsafe(48))"
# copie o valor para JWT_SECRET no .env

# 3. banco (PostgreSQL + pgAdmin)
docker compose up -d

# 4. migrations e seed
alembic upgrade head
python -m app.infrastructure.seed

# 5. iniciar a API
fastapi dev app/main.py            # http://localhost:8000
# alternativa: uvicorn app.main:app --reload
```

- Swagger/OpenAPI: http://localhost:8000/docs
- pgAdmin: http://localhost:5050 (login em `.env`: `PGADMIN_EMAIL` / `PGADMIN_PASSWORD`).
  O servidor "Raizes do Nordeste" ja vem cadastrado; a senha do banco e a `POSTGRES_PASSWORD` do `.env`.
  Se mudar `POSTGRES_USER` ou `POSTGRES_DB`, ajuste tambem `docker/pgadmin/servers.json`
  (e recrie o volume: `docker compose down -v`).

### Variaveis de ambiente (.env)

| Variavel             | Descricao                                            |
| -------------------- | ---------------------------------------------------- |
| `DATABASE_URL`       | URL do Postgres (`postgresql+psycopg://...`)         |
| `JWT_SECRET`         | Chave de assinatura do JWT (gere uma aleatoria)      |
| `JWT_ALGORITHM`      | Algoritmo do JWT (padrao `HS256`)                    |
| `JWT_EXPIRE_MINUTES` | Expiracao do token em minutos (padrao `60`)          |
| `POSTGRES_*`         | Usuario/senha/banco/porta usados pelo docker compose |
| `PGADMIN_*`          | Credenciais do pgAdmin                               |

## Usuarios do seed

Todos com a senha `Senha@123`:

| E-mail                 | Perfil    | Observacao                        |
| ---------------------- | --------- | --------------------------------- |
| `cliente@raizes.com`   | CLIENTE   | consentimento de fidelidade ativo |
| `atendente@raizes.com` | ATENDENTE |                                   |
| `cozinha@raizes.com`   | COZINHA   | muda status de pedidos            |
| `gerente@raizes.com`   | GERENTE   | produtos/estoque                  |
| `admin@raizes.com`     | ADMIN     | unidades e anonimizacao LGPD      |

O seed tambem cria 2 unidades, 5 produtos (cardapio) e estoque inicial de 50 por produto/unidade.

## Testes

```bash
pytest
```

Os testes rodam contra um SQLite em memoria (nao precisam do Postgres) e cobrem
autenticacao/autorizacao, validacoes, regras de estoque, o fluxo pedido -> pagamento
(aprovado/recusado/timeout), transicoes de status, cancelamento com devolucao de estoque,
fidelidade e auditoria. Sao 25 cenarios automatizados (ver `tests/`).

### Colecao Insomnia (ordem sugerida)

Importar `insomnia/raizes_do_nordeste_insomnia.json` no Insomnia/Insomnium. Ambiente **Local**
ja traz `base_url`, `unidadeId`, `produtoId` e campos `token`/`pedidoId` para preencher:

1. **01 - Auth / Login valido**: copie `accessToken` para a variavel de ambiente `token`.
2. **06 - Pedidos / Criar pedido valido**: copie o `id` retornado para a variavel `pedidoId`.
3. **07 - Pagamentos / Pagamento mock APROVADO**: muda o pedido para `PAGO`.
4. **06 - Pedidos / Atualizar status**: faca login como cozinha e atualize `token` para
   mover `EM_PREPARO -> PRONTO -> ENTREGUE`.
5. Pastas de erro (sem token, 403, 422, 404, 409, pagamento recusado/timeout) para os negativos.

## Arquitetura (camadas)

| Camada         | Pasta                | Responsabilidade                                      |
| -------------- | -------------------- | ----------------------------------------------------- |
| Domain         | `app/domain`         | Entidades, enums e regras de negocio                  |
| Application    | `app/application`    | Casos de uso (services) e DTOs/schemas                |
| Infrastructure | `app/infrastructure` | Banco, repositorios, gateway de pagamento mock, seed  |
| API            | `app/api`            | Rotas, autenticacao/autorizacao, contratos            |
| Core           | `app/core`           | Configuracao, seguranca (hash e JWT) e padrao de erro |

As entidades de dominio sao mapeadas direto com SQLAlchemy (sem camada extra de mapeamento),
para simplificar. A persistencia e real (CRUD no banco), com transacoes por caso de uso.

## Endpoints (resumo)

Documentacao completa e interativa no Swagger (`/docs`). Principais recursos:

| Recurso       | Endpoints                                                                                                   | Auth/Perfil                      |
| ------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `/auth`       | `POST /auth/login`, `GET /auth/me`                                                                          | publico / JWT                    |
| `/usuarios`   | `POST /usuarios`, `GET /usuarios`, `GET /usuarios/{id}`, `POST /usuarios/{id}/anonimizar`                   | cadastro publico; resto GER/ADM  |
| `/unidades`   | `POST`, `GET`, `GET /{id}`                                                                                  | leitura publica; criar ADMIN     |
| `/produtos`   | `POST`, `GET`, `GET /{id}`, `PATCH /{id}`                                                                   | leitura publica; escrita GER/ADM |
| `/estoque`    | `POST`, `GET /unidades/{id}`, `GET /unidades/{id}/produtos/{pid}`, `.../entradas`, `.../saidas`             | escrita GER/ADM                  |
| `/pedidos`    | `POST`, `GET` (filtra `?canalPedido=`&`?status=`), `GET /{id}`, `PATCH /{id}/status`, `POST /{id}/cancelar` | JWT; status: operacao            |
| `/pagamentos` | `POST /pagamentos`, `GET /pagamentos/pedidos/{id}`                                                          | JWT                              |
| `/fidelidade` | `GET /fidelidade/saldo`, `POST /fidelidade/resgates`, `GET /fidelidade/historico`                           | JWT                              |

### Multicanalidade

`canalPedido` (ENUM: `APP`, `TOTEM`, `BALCAO`, `PICKUP`, `WEB`) e **obrigatorio** na criacao do
pedido (ausencia/invalido -> 422 padronizado) e e persistido no pedido. A listagem permite
filtrar por canal: `GET /pedidos?canalPedido=TOTEM`.

### Pagamento mock

Nao ha provedor real. O metodo controla o resultado (deterministico, facilita o teste):

- `MOCK` -> aprovado (pedido vai para `PAGO`, credita pontos se houver consentimento)
- `MOCK_FALHA` -> recusado (pedido segue `AGUARDANDO_PAGAMENTO`)
- `MOCK_TIMEOUT` -> indisponibilidade do gateway -> `503` (tolerancia a falha; pode tentar de novo)

A resposta devolve `status` e o `payloadResposta` retornado pelo gateway.

### Padrao de erro (todas as falhas)

```json
{
  "error": "ESTOQUE_INSUFICIENTE",
  "message": "Nao ha quantidade suficiente para um ou mais itens.",
  "details": [{ "field": "produto 1", "issue": "Disponivel: 1" }],
  "timestamp": "2026-02-05T12:00:00Z",
  "path": "/pedidos"
}
```

Status codes usados: 200, 201, 204, 400/422 (validacao), 401 (sem/invalido token),
403 (sem permissao), 404 (nao encontrado), 409 (conflito/regra de negocio), 503 (gateway).

## Seguranca e LGPD

- **Senha**: armazenada com hash **bcrypt**; nunca retornada nas respostas.
- **Autenticacao**: JWT (Bearer) com expiracao configuravel.
- **Autorizacao**: por perfil (`CLIENTE`, `ATENDENTE`, `COZINHA`, `GERENTE`, `ADMIN`) aplicada nos endpoints.
- **Minimizacao / finalidade**: o cadastro coleta apenas nome, e-mail e senha; fidelidade exige
  **consentimento** explicito (`consentimentoFidelidade`), registrado com data.
- **Direito ao esquecimento**: `POST /usuarios/{id}/anonimizar` (ADMIN) remove dados pessoais
  mantendo a integridade referencial.
- **Auditoria**: acoes sensiveis (criar pedido, mudar status, cancelar, pagamento, movimentacao
  de estoque, resgate de pontos) sao registradas em `log_auditoria`.

## Documentacao e diagramas

- Swagger/OpenAPI gerado automaticamente em `/docs` (reflete os endpoints reais).
- Diagramas (PlantUML) em `docs/diagramas/`: **DER**, **classes** (dominio) e **sequencia**
  do fluxo critico (pedido -> pagamento -> status).
