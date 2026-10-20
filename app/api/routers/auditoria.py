from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import exigir_perfil, get_db
from app.api.responses import respostas
from app.application.schemas.auditoria_schemas import LogAuditoriaResposta
from app.application.services.auditoria_service import AuditoriaService
from app.domain.enums import Perfil

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> AuditoriaService:
    return AuditoriaService(db)


@router.get("", response_model=list[LogAuditoriaResposta],
            dependencies=[Depends(exigir_perfil(Perfil.ADMIN))],
            responses=respostas(401, 403))
def listar(
    entidade: str | None = Query(None, description="Filtra por entidade (ex.: pedido, usuario)"),
    limite: int = Query(50, ge=1, le=100),
    deslocamento: int = Query(0, ge=0),
    service: AuditoriaService = Depends(get_service),
):
    """ Consulta a trilha de auditoria (restrito a ADMIN - dado sensivel/LGPD)."""
    return service.listar(limite, deslocamento, entidade)
