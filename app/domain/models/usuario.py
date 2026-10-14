from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.errors import AppError
from app.domain.base import Base
from app.domain.enums import Perfil


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("saldo_pontos >= 0", name="saldo_nao_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unidadeId: Mapped[int | None] = mapped_column("unidade_id", ForeignKey("unidade.id"))
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    _senhaHash: Mapped[str] = mapped_column("senha_hash", String(255))
    perfil: Mapped[Perfil] = mapped_column(Enum(Perfil, native_enum=False, length=30))
    _saldoPontos: Mapped[int] = mapped_column("saldo_pontos", default=0)
    consentimentoLgpd: Mapped[bool] = mapped_column("consentimento_lgpd", default=False)
    consentimentoFidelidade: Mapped[bool] = mapped_column(
        "consentimento_fidelidade", default=False
    )
    consentimentoData: Mapped[datetime | None] = mapped_column(
        "consentimento_data", DateTime(timezone=True)
    )
    createdAt: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=func.now()
    )
    anonimizadoEm: Mapped[datetime | None] = mapped_column(
        "anonimizado_em", DateTime(timezone=True)
    )

    def __init__(self, nome: str, email: str, senhaHash: str, perfil: Perfil,
                 unidadeId: int | None = None, saldoPontos: int = 0,
                 consentimentoLgpd: bool = False, consentimentoFidelidade: bool = False):
        if saldoPontos < 0:
            raise ValueError("Saldo de pontos nao pode ser negativo.")

        self.nome = nome
        self.email = email
        self._senhaHash = senhaHash
        self.perfil = perfil
        self.unidadeId = unidadeId
        self._saldoPontos = saldoPontos
        self.consentimentoLgpd = consentimentoLgpd
        self.consentimentoFidelidade = consentimentoFidelidade
        if consentimentoFidelidade or consentimentoLgpd:
            self.consentimentoData = datetime.now(timezone.utc)

    @property
    def senhaHash(self) -> str:
        return self._senhaHash

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
                "Usuario nao consentiu com o programa de fidelidade.",
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
                "Usuario nao consentiu com o programa de fidelidade.",
            )
        if pontos > self._saldoPontos:
            raise AppError(
                409, "SALDO_INSUFICIENTE",
                f"Saldo insuficiente: disponivel {self._saldoPontos}, solicitado {pontos}.",
            )
        self._saldoPontos -= pontos

    def anonimizar(self) -> None:
        """ Remove dados pessoais mantendo a linha para integridade referencial."""
        if self.id is None:
            raise RuntimeError("Impossível anonimizar um usuario não salvo no banco.")
        self.nome = "Usuario Anonimizado"
        self.email = f"anonimo_{self.id}@anonimizado.invalid"
        self._senhaHash = ""
        self._saldoPontos = 0
        self.consentimentoFidelidade = False
        self.consentimentoLgpd = False
        self.anonimizadoEm = datetime.now(timezone.utc)
