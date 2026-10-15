from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.schemas.unidade_schemas import UnidadeCriar
from app.core.errors import AppError
from app.domain.models.unidade import Unidade
from app.infrastructure.repositories.unidade_repository import UnidadeRepository


class UnidadeService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = UnidadeRepository(session)

    def criar(self, dados: UnidadeCriar) -> Unidade:
        unidade = Unidade(
            nome=dados.nome,
            tipo=dados.tipo,
            cnpj=dados.cnpj,
            endereco=dados.endereco,
        )
        try:
            self.repo.adicionar(unidade)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            raise AppError(409, "CNPJ_JA_CADASTRADO", "Ja existe uma unidade com este CNPJ.")
        return unidade

    def buscar(self, unidadeId: int) -> Unidade:
        unidade = self.repo.obterPorId(unidadeId)
        if unidade is None:
            raise AppError(404, "UNIDADE_NAO_ENCONTRADA", f"Unidade {unidadeId} nao encontrada.")
        return unidade

    def listar(self, limite: int, deslocamento: int) -> list[Unidade]:
        return self.repo.listar(limite, deslocamento)
