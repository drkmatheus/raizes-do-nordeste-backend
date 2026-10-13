from fastapi import FastAPI

from app.api.routers import api_router
from app.core.errors import register_exception_handlers

app = FastAPI(
    title="Raizes do Nordeste - API",
    version="0.1.0",
    description="API Back-end para rede Raizes do Nordeste.",
)

register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health", tags=["Infra"])
def health():
    return {"status": "ok"}
