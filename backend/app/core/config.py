from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LAB_DATABASE_URL: str = "postgresql+psycopg2://luca@localhost:5432/laboratorio_contenido"
    LAB_DATABASE_URL_TEST: str = "postgresql+psycopg2://luca@localhost:5432/laboratorio_contenido_test"
    LAB_INGEST_TOKEN: str = "dev-ingest-token-change-me"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
