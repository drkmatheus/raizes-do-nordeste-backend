"""Seed: unidades, produtos, estoque e usuarios de cada perfil.

Rode com: python -m app.infrastructure.seed
Idempotente: nao duplica se ja houver dados (checa por e-mail/cnpj/nome).
"""
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_senha
from app.domain.enums import Perfil
from app.domain.models.estoque import Estoque
from app.domain.models.produto import Produto
from app.domain.models.unidade import Unidade
from app.domain.models.usuario import Usuario
from app.infrastructure.database import SessionLocal

SENHA_PADRAO = "Senha@123"


def _get_or_create(session, model, chave: dict, **extra):
    stmt = select(model).filter_by(**chave)
    obj = session.scalars(stmt).one_or_none()
    if obj is None:
        obj = model(**chave, **extra)
        session.add(obj)
        session.flush()
    return obj


def run() -> None:
    with SessionLocal() as session:
        # --- Unidades ---
        matriz = _get_or_create(
            session, Unidade, {"cnpj": "12.345.678/0001-90"},
            nome="Raizes - Matriz Recife", tipo="MATRIZ", endereco="Av. Boa Viagem, 1000",
        )
        filial = _get_or_create(
            session, Unidade, {"cnpj": "12.345.678/0002-71"},
            nome="Raizes - Filial Olinda", tipo="FILIAL", endereco="Rua do Sol, 200",
        )

        # --- Usuarios (um por perfil) ---
        usuarios = [
            ("Ana Cliente", "cliente@raizes.com", Perfil.CLIENTE, None, True, True),
            ("Bruno Atendente", "atendente@raizes.com", Perfil.ATENDENTE, matriz.id, False, False),
            ("Carla Cozinha", "cozinha@raizes.com", Perfil.COZINHA, matriz.id, False, False),
            ("Diego Gerente", "gerente@raizes.com", Perfil.GERENTE, matriz.id, False, False),
            ("Eva Admin", "admin@raizes.com", Perfil.ADMIN, None, False, False),
        ]
        for nome, email, perfil, unidadeId, lgpd, fidelidade in usuarios:
            if session.scalars(select(Usuario).where(Usuario.email == email)).one_or_none():
                continue
            session.add(Usuario(
                nome=nome, email=email, senhaHash=hash_senha(SENHA_PADRAO),
                perfil=perfil, unidadeId=unidadeId,
                consentimentoLgpd=lgpd, consentimentoFidelidade=fidelidade,
            ))

        # --- Produtos (cardapio nordestino) ---
        produtos_dados = [
            ("Baiao de Dois", Decimal("28.90"), "Arroz, feijao verde, queijo coalho", "Prato"),
            ("Carne de Sol com Macaxeira", Decimal("42.50"), "Carne de sol com macaxeira frita", "Prato"),
            ("Acaraje", Decimal("18.00"), "Bolinho de feijao fradinho com vatapa", "Petisco"),
            ("Tapioca Recheada", Decimal("15.00"), "Tapioca com queijo coalho e carne seca", "Lanche"),
            ("Caldo de Cana", Decimal("8.00"), "Caldo de cana gelado 500ml", "Bebida"),
        ]
        produtos = []
        for nome, preco, desc, cat in produtos_dados:
            p = _get_or_create(session, Produto, {"nome": nome},
                               preco=preco, descricao=desc, categoria=cat, ativo=True)
            produtos.append(p)

        # --- Estoque por unidade ---
        for unidade in (matriz, filial):
            for produto in produtos:
                existe = session.scalars(
                    select(Estoque).where(
                        Estoque.unidadeId == unidade.id, Estoque.produtoId == produto.id
                    )
                ).one_or_none()
                if existe is None:
                    session.add(Estoque(unidadeId=unidade.id, produtoId=produto.id,
                                        quantidade=50, disponivel=True))

        session.commit()
        print("Seed aplicado. Usuarios criados com senha:", SENHA_PADRAO)
        print("  cliente@raizes.com / atendente@raizes.com / cozinha@raizes.com")
        print("  gerente@raizes.com / admin@raizes.com")


if __name__ == "__main__":
    run()
