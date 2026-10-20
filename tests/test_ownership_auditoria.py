""" Cobertura das mudancas de seguranca/LGPD/coerencia:

- Ownership de pedidos e pagamentos (CLIENTE so acessa o proprio).
- Endpoint de leitura de auditoria (restrito a ADMIN).
- Logs de consentimento (cadastro) e anonimizacao.
- GERENTE restrito a propria unidade ao operar status (ADMIN global).
"""

def _criar_pedido(client, header, seed, quantidade=1, canal="APP"):
    body = {
        "canalPedido": canal,
        "unidadeId": seed["unidadeId"],
        "itens": [{"produtoId": seed["produtoId"], "quantidade": quantidade}],
    }
    return client.post("/pedidos", json=body, headers=header)


def _registrar_e_logar(client, email="cliente2@teste.com"):
    client.post("/usuarios", json={"nome": "Cliente Dois", "email": email,
                                   "senha": "Senha@123", "consentimentoLgpd": True})
    token = client.post("/auth/login", json={"email": email, "senha": "Senha@123"}).json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


# ---- Ownership de pedidos ----

def test_cliente_nao_ve_pedido_de_outro_cliente(client, auth_header, seed):
    dono = auth_header("cliente")
    outro = _registrar_e_logar(client)
    pedido = _criar_pedido(client, dono, seed).json()

    resp = client.get(f"/pedidos/{pedido['id']}", headers=outro)
    assert resp.status_code == 404  # nao revela existencia


def test_cliente_so_lista_os_proprios_pedidos(client, auth_header, seed):
    dono = auth_header("cliente")
    outro = _registrar_e_logar(client)
    _criar_pedido(client, dono, seed)

    assert client.get("/pedidos", headers=outro).json() == []
    assert len(client.get("/pedidos", headers=dono).json()) >= 1


def test_staff_ve_todos_os_pedidos(client, auth_header, seed):
    dono = auth_header("cliente")
    gerente = auth_header("gerente")
    _criar_pedido(client, dono, seed)

    assert len(client.get("/pedidos", headers=gerente).json()) >= 1


# ---- Ownership de pagamentos ----

def test_cliente_nao_paga_pedido_alheio(client, auth_header, seed):
    dono = auth_header("cliente")
    outro = _registrar_e_logar(client)
    pedido = _criar_pedido(client, dono, seed).json()

    resp = client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"},
                       headers=outro)
    assert resp.status_code == 404


def test_cliente_nao_ve_pagamentos_alheios(client, auth_header, seed):
    dono = auth_header("cliente")
    outro = _registrar_e_logar(client)
    pedido = _criar_pedido(client, dono, seed).json()
    client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"}, headers=dono)

    resp = client.get(f"/pagamentos/pedidos/{pedido['id']}", headers=outro)
    assert resp.status_code == 404


# ---- Endpoint de auditoria ----

def test_auditoria_exige_admin(client, auth_header, seed):
    assert client.get("/auditoria", headers=auth_header("cliente")).status_code == 403
    assert client.get("/auditoria", headers=auth_header("gerente")).status_code == 403


def test_auditoria_admin_le_logs(client, auth_header, seed):
    _criar_pedido(client, auth_header("cliente"), seed)
    resp = client.get("/auditoria?entidade=pedido", headers=auth_header("admin"))
    assert resp.status_code == 200
    assert any(log["acao"] == "PEDIDO_CRIADO" for log in resp.json())


# ---- Logs LGPD ----

def test_cadastro_registra_consentimento(client, auth_header, seed):
    _registrar_e_logar(client, email="cliente3@teste.com")
    logs = client.get("/auditoria?entidade=usuario", headers=auth_header("admin")).json()
    assert any(log["acao"] == "CONSENTIMENTO_REGISTRADO" for log in logs)


def test_anonimizacao_gera_log(client, auth_header, seed):
    admin = auth_header("admin")
    alvo = seed["usuarios"]["cliente"]
    assert client.post(f"/usuarios/{alvo}/anonimizar", headers=admin).status_code == 204

    logs = client.get("/auditoria?entidade=usuario", headers=admin).json()
    assert any(log["acao"] == "USUARIO_ANONIMIZADO" and log["entidadeId"] == alvo
               for log in logs)


# ---- GERENTE restrito a unidade ----

def test_gerente_de_outra_unidade_nao_atualiza_status(client, auth_header, seed, db_session):
    from app.domain.models.unidade import Unidade
    from app.domain.models.usuario import Usuario
    from app.core.security import hash_senha
    from app.domain.enums import Perfil

    # Gerente vinculado a OUTRA unidade.
    outra = Unidade(nome="Filial", tipo="FILIAL", cnpj="11.111.111/0001-11")
    db_session.add(outra)
    db_session.flush()
    db_session.add(Usuario(nome="Ger Filial", email="gerfilial@teste.com",
                           senhaHash=hash_senha("Senha@123"), perfil=Perfil.GERENTE,
                           unidadeId=outra.id, consentimentoLgpd=True))
    db_session.commit()

    cliente = auth_header("cliente")
    pedido = _criar_pedido(client, cliente, seed).json()
    client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"}, headers=cliente)

    token = client.post("/auth/login",
                        json={"email": "gerfilial@teste.com", "senha": "Senha@123"}).json()["accessToken"]
    ger_filial = {"Authorization": f"Bearer {token}"}
    resp = client.patch(f"/pedidos/{pedido['id']}/status",
                        json={"status": "EM_PREPARO"}, headers=ger_filial)
    assert resp.status_code == 403
    assert resp.json()["error"] == "SEM_PERMISSAO"


def test_admin_atualiza_status_de_qualquer_unidade(client, auth_header, seed):
    cliente = auth_header("cliente")
    admin = auth_header("admin")
    pedido = _criar_pedido(client, cliente, seed).json()
    client.post("/pagamentos", json={"pedidoId": pedido["id"], "metodo": "MOCK"}, headers=cliente)

    resp = client.patch(f"/pedidos/{pedido['id']}/status",
                        json={"status": "EM_PREPARO"}, headers=admin)
    assert resp.status_code == 200
    assert resp.json()["status"] == "EM_PREPARO"
