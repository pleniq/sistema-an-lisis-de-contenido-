from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base de datos
    LAB_DATABASE_URL: str = "postgresql+psycopg2://luca@localhost:5432/laboratorio_contenido"
    LAB_DATABASE_URL_TEST: str = "postgresql+psycopg2://luca@localhost:5432/laboratorio_contenido_test"

    # Token máquina-a-máquina para la ingesta (n8n lo manda en X-Ingest-Token)
    LAB_INGEST_TOKEN: str = "dev-ingest-token-change-me"

    # Webhooks de n8n (vacíos = n8n no configurado → se reporta apagado sin llamar)
    LAB_N8N_PING_WEBHOOK_URL: Optional[str] = None
    LAB_N8N_INGEST_WEBHOOK_URL: Optional[str] = None

    # Guardas del sync on-demand
    LAB_SYNC_STALE_MINUTES: int = 5    # < esto = "fresco", no re-sincroniza al abrir
    LAB_SYNC_STUCK_MINUTES: int = 10   # run 'running' más viejo que esto = muerto
    LAB_N8N_PING_TIMEOUT_SECONDS: float = 2.0

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
