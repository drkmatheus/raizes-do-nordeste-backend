import pytest
import jwt

from app.core.security import (
    criar_access_token,
    decodificar_token,
    hash_senha,
    verificar_senha,
)


def test_hash_nao_guarda_senha_em_texto_puro():
    senha = "Senha@123"
    senha_hash = hash_senha(senha)
    assert senha_hash != senha
    assert verificar_senha(senha, senha_hash)
    assert not verificar_senha("outra", senha_hash)


def test_token_carrega_usuario_e_perfil():
    token = criar_access_token(10, "CLIENTE")
    dados = decodificar_token(token)
    assert dados["sub"] == "10"
    assert dados["perfil"] == "CLIENTE"


def test_token_adulterado_e_rejeitado():
    token = criar_access_token(10, "CLIENTE")
    with pytest.raises(jwt.InvalidTokenError):
        decodificar_token(token + "x")
