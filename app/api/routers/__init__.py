from fastapi import APIRouter

from app.api.routers import (
    auditoria,
    auth,
    estoque,
    fidelidade,
    pagamentos,
    pedidos,
    produtos,
    unidades,
    usuarios,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(unidades.router, prefix="/unidades", tags=["Unidades"])
api_router.include_router(produtos.router, prefix="/produtos", tags=["Produtos"])
api_router.include_router(estoque.router, prefix="/estoque", tags=["Estoque"])
api_router.include_router(pedidos.router, prefix="/pedidos", tags=["Pedidos"])
api_router.include_router(pagamentos.router, prefix="/pagamentos", tags=["Pagamentos"])
api_router.include_router(fidelidade.router, prefix="/fidelidade", tags=["Fidelidade"])
api_router.include_router(auditoria.router, prefix="/auditoria", tags=["Auditoria"])
