"""Cenarios do fluxo critico: pedido -> pagamento mock -> status.

Cobre os cenarios obrigatorios do plano de testes (positivos e negativos).
"""


def _criar_pedido(client, header, seed, quantidade=2, canal="TOTEM", produto=None):
    body = {
        "canalPedido": canal,
        "unidadeId": seed["unidadeId"],
        "itens": [{"produtoId": produto or seed["produtoId"], "quantidade": quantidade}],
    }
    return client.post("/pedidos", json=body, headers=header)


# ---- Autenticacao / autorizacao ----

def test_login_valido_retorna_token(client, seed):  # T01
    resp = client.post("/auth/login", json={"email": "cliente@teste.com", "senha": "Senha@123"})
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["accessToken"]
    assert corpo["user"]["perfil"] == "CLIENTE"
    assert "senha" not in corpo["user"] and "senhaHash" not in corpo["user"]


def test_login_invalido_retorna_401(client, seed):  # T02
    resp = client.post("/auth/login", json={"email": "cliente@teste.com", "senha": "errada"})
    assert resp.status_code == 401
    assert resp.json()["error"] == "CREDENCIAIS_INVALIDAS"


def test_listar_pedidos_sem_token_retorna_401(client, seed):  # T03
    resp = client.get("/pedidos")
    assert resp.status_code == 401
    assert set(resp.json()) == {"error", "message", "details", "timestamp", "path"}


def test_cliente_sem_permissao_para_criar_produto_retorna_403(client, auth_header):  # T04
    resp = client.post("/produtos", json={"nome": "X", "preco": 1.0},
                       headers=auth_header("cliente"))
    assert resp.status_code == 403
    assert resp.json()["error"] == "SEM_PERMISSAO"


# ---- Validacao de dados ----

def test_pedido_sem_canal_retorna_422(client, auth_header, seed):  # T05
    body = {"unidadeId": seed["unidadeId"],
            "itens": [{"produtoId": seed["produtoId"], "quantidade": 1}]}
    resp = client.post("/pedidos", json=body, headers=auth_header("cliente"))
    assert resp.status_code == 422
    assert resp.json()["error"] == "DADOS_INVALIDOS"


def test_pedido_canal_invalido_retorna_422(client, auth_header, seed):  # T06
    body = {"canalPedido": "DRIVE_THRU", "unidadeId": seed["unidadeId"],
            "itens": [{"produtoId": seed["produtoId"], "quantidade": 1}]}
    resp = client.post("/pedidos", json=body, headers=auth_header("cliente"))
    assert resp.status_code == 422


def test_cadastro_email_invalido_retorna_422(client):  # T07
    resp = client.post("/usuarios", json={"nome": "X", "email": "nao-eh-email",
                                          "senha": "Senha@123"})
    assert resp.status_code == 422


# ---- Regras de negocio do fluxo ----

def test_criar_pedido_valido_retorna_201(client, auth_header, seed):  # T08
    resp = _criar_pedido(client, auth_header("cliente"), seed, quantidade=2)
    assert resp.status_code == 201, resp.text
    corpo = resp.json()
    assert corpo["status"] == "AGUARDANDO_PAGAMENTO"
    assert corpo["canalPedido"] == "TOTEM"
    assert corpo["valorTotal"] == "57.80"  # 2 * 28.90


def test_pedido_produto_inexistente_retorna_404(client, auth_header, seed):  # T09
    resp = _criar_pedido(client, auth_header("cliente"), seed, produto=999999)
    assert resp.status_code == 404
    assert resp.json()["error"] == "PRODUTO_NAO_ENCONTRADO"


def test_pedido_estoque_insuficiente_retorna_409(client, auth_header, seed):  # T10
    resp = _criar_pedido(client, auth_header("cliente"), seed, quantidade=999)
    assert resp.status_code == 409
    assert resp.json()["error"] == "ESTOQUE_INSUFICIENTE"


def test_pedido_com_produto_repetido_valida_quantidade_total_e_nao_baixa_estoque(
    client, auth_header, seed
):
    header = auth_header("cliente")
    body = {
        "canalPedido": "TOTEM",
        "unidadeId": seed["unidadeId"],
        "itens": [
            {"produtoId": seed["produtoId"], "quantidade": 6},
            {"produtoId": seed["produtoId"], "quantidade": 6},
        ],
    }

    resp = client.post("/pedidos", json=body, headers=header)

    assert resp.status_code == 409
    assert resp.json()["error"] == "ESTOQUE_INSUFICIENTE"
    saldo = client.get(
        f"/estoque/unidades/{seed['unidadeId']}/produtos/{seed['produtoId']}",
        headers=auth_header("gerente"),
    )
    assert saldo.status_code == 200
    assert saldo.json()["quantidade"] == 10


def test_filtro_por_canal(client, auth_header, seed):  # T11
    _criar_pedido(client, auth_header("cliente"), seed, quantidade=1, canal="TOTEM")
    _criar_pedido(client, auth_header("cliente"), seed, quantidade=1, canal="APP")
    resp = client.get("/pedidos?canalPedido=TOTEM", headers=auth_header("cliente"))
    assert resp.status_code == 200
    assert all(p["canalPedido"] == "TOTEM" for p in resp.json())


def test_idempotencia_mesmo_request_id(client, auth_header, seed):  # T12
    header = auth_header("cliente")
    body = {"canalPedido": "APP", "unidadeId": seed["unidadeId"], "requestId": "abc-123",
            "itens": [{"produtoId": seed["produtoId"], "quantidade": 1}]}
    r1 = client.post("/pedidos", json=body, headers=header)
    r2 = client.post("/pedidos", json=body, headers=header)
    assert r1.status_code == 201
    assert r2.status_code == 200  # nao duplica
    assert r1.json()["id"] == r2.json()["id"]


# ---- Pagamento mock e atualizacao de status ----

def test_pagamento_aprovado_atualiza_pedido_para_pago(client, auth_header, seed):  # T13
    header = auth_header("cliente")
    pedido = _criar_pedido(client, header, seed, quantidade=1).json()
    resp = client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"},
                       headers=header)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APROVADO"

    atual = client.get(f"/pedidos/{pedido['id']}", headers=header).json()
    assert atual["status"] == "PAGO"


def test_pagamento_recusado_mantem_aguardando(client, auth_header, seed):  # T14
    header = auth_header("cliente")
    pedido = _criar_pedido(client, header, seed, quantidade=1).json()
    resp = client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK_FALHA"},
                       headers=header)
    assert resp.status_code == 200
    assert resp.json()["status"] == "RECUSADO"

    atual = client.get(f"/pedidos/{pedido['id']}", headers=header).json()
    assert atual["status"] == "AGUARDANDO_PAGAMENTO"


def test_pagamento_timeout_retorna_503(client, auth_header, seed):  # T15
    header = auth_header("cliente")
    pedido = _criar_pedido(client, header, seed, quantidade=1).json()
    resp = client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK_TIMEOUT"},
                       headers=header)
    assert resp.status_code == 503
    assert resp.json()["error"] == "GATEWAY_INDISPONIVEL"


def test_fluxo_status_cozinha_ate_entregue(client, auth_header, seed):  # T16
    cliente = auth_header("cliente")
    cozinha = auth_header("cozinha")
    pedido = _criar_pedido(client, cliente, seed, quantidade=1).json()
    client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"}, headers=cliente)

    for novo in ("EM_PREPARO", "PRONTO", "ENTREGUE"):
        resp = client.patch(f"/pedidos/{pedido['id']}/status",
                            json={"status": novo}, headers=cozinha)
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == novo


def test_transicao_invalida_retorna_409(client, auth_header, seed):  # T17
    cliente = auth_header("cliente")
    cozinha = auth_header("cozinha")
    pedido = _criar_pedido(client, cliente, seed, quantidade=1).json()
    # Ainda AGUARDANDO_PAGAMENTO: nao pode ir direto para PRONTO.
    resp = client.patch(f"/pedidos/{pedido['id']}/status",
                        json={"status": "PRONTO"}, headers=cozinha)
    assert resp.status_code == 409
    assert resp.json()["error"] == "TRANSICAO_INVALIDA"


def test_cancelar_devolve_estoque(client, auth_header, seed):  # T18
    cliente = auth_header("cliente")
    gerente = auth_header("gerente")
    saldo_antes = client.get(
        f"/estoque/unidades/{seed['unidadeId']}/produtos/{seed['produtoId']}",
        headers=gerente,
    ).json()["quantidade"]

    pedido = _criar_pedido(client, cliente, seed, quantidade=3).json()
    resp = client.post(f"/pedidos/{pedido['id']}/cancelar", headers=gerente)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELADO"

    saldo_depois = client.get(
        f"/estoque/unidades/{seed['unidadeId']}/produtos/{seed['produtoId']}",
        headers=gerente,
    ).json()["quantidade"]
    assert saldo_depois == saldo_antes  # estoque devolvido


# ---- Fidelidade ----

def test_pagamento_credita_pontos_com_consentimento(client, auth_header, seed):  # T19
    header = auth_header("cliente")
    pedido = _criar_pedido(client, header, seed, quantidade=1).json()
    client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"}, headers=header)

    saldo = client.get("/fidelidade/saldo", headers=header).json()
    assert saldo["saldoPontos"] == 28  # int(28.90)


# ---- Auditoria ----

def test_criar_pedido_gera_log_auditoria(client, auth_header, seed, db_session):  # T20
    from app.domain.models.log_auditoria import LogAuditoria
    from sqlalchemy import select

    _criar_pedido(client, auth_header("cliente"), seed, quantidade=1)
    logs = db_session.scalars(
        select(LogAuditoria).where(LogAuditoria.acao == "PEDIDO_CRIADO")
    ).all()
    assert len(logs) >= 1
