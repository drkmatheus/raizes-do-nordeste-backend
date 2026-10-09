from sqlalchemy import CheckConstraint, Enum, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from base import Base
from enums import Perfil
from core.errors import AppError


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("saldo_pontos >= 0", name="ck_usuario_saldo_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    _senhaHash: Mapped[str] = mapped_column("senha_hash", String(255))
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil, native_enum=False, length=30))
    _saldoPontos: Mapped[int] = mapped_column("saldo_pontos", default=0)
    consentimentoFidelidade: Mapped[bool] = mapped_column(
        "consentimento_fidelidade", default=False
    )

    def __init__(self, nome: str, email: str, senhaHash: str, perfil: Perfil,
                 saldoPontos: int = 0, consentimentoFidelidade: bool = False):
        if saldoPontos < 0:
            raise ValueError("Saldo de pontos não pode ser negativo.")

        self.nome = nome
        self.email = email
        self._senhaHash = senhaHash
        self.perfil = perfil
        self._saldoPontos = saldoPontos
        self.consentimentoFidelidade = consentimentoFidelidade

    @hybrid_property
    def saldoPontos(self) -> int:
        return self._saldoPontos

    def podeResgatar(self) -> bool:
        return self._saldoPontos > 0 and self.consentimentoFidelidade

    def acumularPontos(self, pontos: int) -> None:
        if pontos <= 0:
            raise AppError(
                422, "PONTOS_INVALIDOS", "A quantidade de pontos deve ser maior que zero.",
                [{"field": "pontos", "issue": "deve ser maior que zero"}],
            )
        if not self.consentimentoFidelidade:
            raise AppError(
                403, "CONSENTIMENTO_NAO_CONCEDIDO",
                "Usuário não consentiu com o programa de fidelidade.",
            )
        self._saldoPontos += pontos

    def resgatarPontos(self, pontos: int) -> None:
        if pontos <= 0:
            raise AppError(
                422, "PONTOS_INVALIDOS", "A quantidade de pontos deve ser maior que zero.",
                [{"field": "pontos", "issue": "deve ser maior que zero"}],
            )
        if not self.consentimentoFidelidade:
            raise AppError(
                403, "CONSENTIMENTO_NAO_CONCEDIDO",
                "Usuário não consentiu com o programa de fidelidade.",
            )
        if pontos > self._saldoPontos:
            raise AppError(
                409, "SALDO_INSUFICIENTE",
                f"Saldo insuficiente: disponível {self._saldoPontos}, solicitado {pontos}.",
            )
        self._saldoPontos -= pontos

    def anonimizar(self) -> None:
        if self.id is None:
            raise RuntimeError("Só é possível anonimizar um usuário já salvo no banco.")
        self.nome = "Usuário Anonimizado"
        self.email = f"anonimo_{self.id}@anonimizado.invalid"
        self._senhaHash = ""
        self._saldoPontos = 0
        self.consentimentoFidelidade = False