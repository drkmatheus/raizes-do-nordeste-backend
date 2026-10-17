CHAVES = {"error", "message", "details", "timestamp", "path"}


def test_rota_inexistente_retorna_erro_padrao(client):
    resposta = client.get("/nao-existe")
    corpo = resposta.json()
    assert resposta.status_code == 404
    assert set(corpo) == CHAVES
    assert corpo["error"] == "NAO_ENCONTRADO"
    assert corpo["path"] == "/nao-existe"
