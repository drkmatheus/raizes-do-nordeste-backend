from fastapi import FastAPI

from app.api.routers import api_router
from app.core.errors import register_exception_handlers

app = FastAPI(
    title="Raizes do Nordeste - API",
    version="0.1.0",
    description="Back-end da rede Raizes do Nordeste (Projeto Multidisciplinar - Trilha Back-End).",
)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}
