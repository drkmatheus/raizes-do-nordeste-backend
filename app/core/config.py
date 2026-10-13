from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="")
    jwt_secret: str = Field(default="")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # extra="ignore": o .env tambem tem variaveis do docker compose (POSTGRES_*, PGADMIN_*)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
