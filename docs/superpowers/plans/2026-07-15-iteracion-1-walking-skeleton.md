# Laboratorio de Contenido — Iteración 1: Walking Skeleton — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task (ejecución inline, con checkpoints). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Probar el pipe end-to-end más fino posible: un batch de métricas (mock de IG) entra por el endpoint de ingesta, se guarda idempotente en Postgres con snapshot diario, y se ve en una tabla en el navegador — sin n8n todavía.

**Architecture:** Backend FastAPI en 3 capas (models / repositories / services / api) sobre PostgreSQL con Alembic, replicando el patrón de PLENIQ. Front React + Vite (estilo NUSA) con una única página que consume `GET /reels`. La ingesta es un endpoint HTTP que en esta iteración se alimenta con un seed de datos mock; n8n se conecta en la Iteración 2.

**Tech Stack:** Python 3.13 · FastAPI 0.136.1 · SQLAlchemy 2.0.49 · Alembic · Pydantic 2.13.4 · psycopg2-binary · PostgreSQL 16 (Homebrew) · React 18 + Vite 6 + TypeScript · pytest + httpx.

## Global Constraints

- **Métricas Graph API (nombres EXACTOS, verificados 2026-07-15):** `reach`, `views`, `likes`, `comments`, `saved`, `shares`, `total_interactions`, `ig_reels_avg_watch_time` (ms), `ig_reels_video_view_total_time` (ms). NO usar `impressions` (deprecado) ni `plays` (renombrado a `views`).
- **Watch times en milisegundos** en la DB (`avg_watch_time_ms`, `total_watch_time_ms`); se exponen segundos en la capa de lectura.
- **Multi-cuenta desde día 1:** todo cuelga de `account_id` aunque haya una sola cuenta.
- **Snapshot idempotente:** UNIQUE(`reel_id`, `snapshot_date`); re-correr el mismo día actualiza la fila, no duplica.
- **La ingesta nunca pisa campos manuales** (`titulo`, `guion`, y las 5 FKs de etiqueta) — solo toca campos de la API.
- **IDs:** `String(36)` UUID4 como PK (patrón PLENIQ).
- **Env con prefijo `LAB_`.** Sin login de usuario en v1; el endpoint de ingesta valida `X-Ingest-Token`.
- **Postgres local por Homebrew** (Docker no está instalado; containerización = deploy/v2). Python `python3.13` para el venv.

---

## Roadmap de iteraciones (visión general)

Cada iteración deja algo usable de punta a punta. Se planifica en detalle la iteración en curso; las siguientes tienen su plan propio al llegar.

- **Iteración 1 (este plan) — Walking skeleton:** DB + ingesta (mock) + `GET /reels` + tabla en el front. Prueba el pipe completo.
- **Iteración 2 — Ingesta real vía n8n + sync on-demand:** `ingest_runs`, `POST /sync/refresh` (lock + liveness ping + frescura), `GET /sync/status`, workflows n8n (ping + ingest), botón "Actualizar" + indicador + auto-refresh al abrir. *(requiere n8n instalado)*
- **Iteración 3 — Etiquetado + análisis "qué funciona":** `PATCH /reels/{id}` (titulo/guion/labels con create-on-the-fly), `GET/POST /labels/{dimension}`, `GET /analysis?group_by=...`, panel de etiquetado inline + filtros/orden + página "qué funciona".
- **Iteración 4 — Export a Claude + detalle:** `POST /reels/export` (markdown token-eficiente), `GET /reels/{id}` (detalle + historial + mini-chart), selección múltiple + "Copiar para Claude", thumbnails y permalink.
- **Iteración 5 — Refresh de token n8n + hardening.**

---

## File Structure (Iteración 1)

**Backend** (`backend/`)
- `backend/requirements.txt` — deps.
- `backend/.env.example` — variables `LAB_`.
- `backend/app/__init__.py`
- `backend/app/core/config.py` — settings pydantic (`LAB_` prefix).
- `backend/app/core/database.py` — engine, `SessionLocal`, `Base`, `get_db`.
- `backend/app/models/__init__.py` — todos los modelos SQLAlchemy.
- `backend/app/schemas/ingest.py` — Pydantic del payload de ingesta.
- `backend/app/schemas/reel.py` — Pydantic del read model de reel.
- `backend/app/repositories/ingest_repository.py` — upsert account/reel/snapshot.
- `backend/app/repositories/reel_repository.py` — lectura de `reel_latest_metrics`.
- `backend/app/services/ingest_service.py` — orquesta el upsert de un batch.
- `backend/app/services/reel_service.py` — arma el read model.
- `backend/app/api/v1/ingest.py` — `POST /ingest/instagram`.
- `backend/app/api/v1/reels.py` — `GET /reels`.
- `backend/app/main.py` — app FastAPI, CORS, routers, `/health`.
- `backend/app/seed_mock.py` — postea un batch mock a la ingesta.
- `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/*` — migraciones.
- `backend/tests/conftest.py` — fixtures de DB de test (Postgres + rollback por test).
- `backend/tests/test_ingest.py`, `backend/tests/test_reels.py`.

**Frontend** (`frontend/`)
- `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`
- `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/lib/api.ts`, `frontend/src/styles.css`

---

### Task 1: Entorno + scaffold backend + `/health`

Deja el backend levantando con Postgres local y un `/health` verde.

**Files:**
- Create: `backend/requirements.txt`, `backend/.env.example`, `backend/app/__init__.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/main.py`, `backend/tests/__init__.py`, `backend/tests/test_health.py`

**Interfaces:**
- Produces: `get_settings() -> Settings` (con `LAB_DATABASE_URL`, `LAB_DATABASE_URL_TEST`, `LAB_INGEST_TOKEN`); `Base`, `get_db()`, `SessionLocal`, `engine` en `app.core.database`; `app` (FastAPI) en `app.main`.

- [ ] **Step 1: Instalar Postgres y crear las bases (una vez).** Confirmar con Luca antes de correr los `brew install`.

```bash
export PATH="/opt/homebrew/bin:$PATH"
brew install postgresql@16
brew services start postgresql@16
# el superusuario local es tu usuario mac (luca), trust auth en localhost, sin password
/opt/homebrew/opt/postgresql@16/bin/createdb laboratorio_contenido
/opt/homebrew/opt/postgresql@16/bin/createdb laboratorio_contenido_test
```

- [ ] **Step 2: Crear el venv con python3.13 e instalar deps.**

`backend/requirements.txt`:
```
fastapi==0.136.1
uvicorn[standard]==0.47.0
sqlalchemy==2.0.49
alembic==1.14.0
pydantic==2.13.4
pydantic-settings==2.14.1
psycopg2-binary==2.9.10
httpx==0.28.1
pytest==8.3.4
```

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 3: Config y database.**

`backend/app/core/config.py`:
```python
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
```

`backend/app/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.LAB_DATABASE_URL, pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

`backend/.env.example`:
```
LAB_DATABASE_URL=postgresql+psycopg2://luca@localhost:5432/laboratorio_contenido
LAB_DATABASE_URL_TEST=postgresql+psycopg2://luca@localhost:5432/laboratorio_contenido_test
LAB_INGEST_TOKEN=dev-ingest-token-change-me
```

`backend/app/__init__.py` y `backend/tests/__init__.py`: vacíos.

- [ ] **Step 4: App FastAPI con `/health`.**

`backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Laboratorio de Contenido API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # v1 sin auth/cookies; '*' + credentials es combo inválido
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Escribir el test de health.**

`backend/tests/test_health.py`:
```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 6: Correr el test (debe pasar).**

Run: `cd backend && source .venv/bin/activate && pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 7: Commit.**

```bash
git add backend/requirements.txt backend/.env.example backend/app backend/tests
git commit -m "feat(backend): scaffold FastAPI + config + health endpoint"
```

---

### Task 2: Modelos SQLAlchemy + migración inicial (schema completo + vista)

**Files:**
- Create: `backend/app/models/__init__.py`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`, `backend/alembic/versions/0001_schema_inicial.py`, `backend/tests/test_schema.py`
- Modify: `backend/tests/conftest.py` (nuevo)

**Interfaces:**
- Produces: modelos `Account`, `Angulo`, `Formato`, `TipoHook`, `Categoria`, `Tema`, `Reel`, `ReelMetricSnapshot`, `IngestRun`; vista SQL `reel_latest_metrics`. Fixture `db` (Session con rollback por test) y `client` (TestClient con `get_db` override) en `conftest.py`.

- [ ] **Step 1: Escribir todos los modelos.**

`backend/app/models/__init__.py`:
```python
import uuid
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, BigInteger, Date, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    ig_user_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class _LabelBase:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Angulo(_LabelBase, Base):
    __tablename__ = "angulos"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_angulos_account_name"),)


class Formato(_LabelBase, Base):
    __tablename__ = "formatos"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_formatos_account_name"),)


class TipoHook(_LabelBase, Base):
    __tablename__ = "tipos_hook"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_tipos_hook_account_name"),)


class Categoria(_LabelBase, Base):
    __tablename__ = "categorias"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_categorias_account_name"),)


class Tema(_LabelBase, Base):
    __tablename__ = "temas"
    __table_args__ = (UniqueConstraint("account_id", "name", name="uq_temas_account_name"),)


class Reel(Base):
    __tablename__ = "reels"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    ig_media_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    permalink: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_product_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # campos manuales (la ingesta NUNCA los pisa)
    titulo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    angulo_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("angulos.id", ondelete="SET NULL"), nullable=True)
    formato_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("formatos.id", ondelete="SET NULL"), nullable=True)
    tipo_hook_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("tipos_hook.id", ondelete="SET NULL"), nullable=True)
    categoria_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True)
    tema_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("temas.id", ondelete="SET NULL"), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    snapshots: Mapped[list["ReelMetricSnapshot"]] = relationship(
        "ReelMetricSnapshot", back_populates="reel", cascade="all, delete-orphan"
    )


class ReelMetricSnapshot(Base):
    __tablename__ = "reel_metric_snapshots"
    __table_args__ = (UniqueConstraint("reel_id", "snapshot_date", name="uq_snapshot_reel_date"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    reel_id: Mapped[str] = mapped_column(String(36), ForeignKey("reels.id", ondelete="CASCADE"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saved: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_interactions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_watch_time_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_watch_time_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    reel: Mapped["Reel"] = relationship("Reel", back_populates="snapshots")


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    account_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    trigger: Mapped[str] = mapped_column(String(16), default="manual")  # 'auto' | 'manual'
    status: Mapped[str] = mapped_column(String(16), default="running")  # running|ok|partial|error
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reels_processed: Mapped[int] = mapped_column(Integer, default=0)
    snapshots_written: Mapped[int] = mapped_column(Integer, default=0)
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

- [ ] **Step 2: Inicializar Alembic y configurarlo.**

```bash
cd backend && source .venv/bin/activate
alembic init alembic
```
Editar `backend/alembic/env.py` para usar la URL de settings y el metadata de `Base`. Reemplazar el cuerpo por:
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import get_settings
from app.core.database import Base
import app.models  # noqa: F401  (registra todos los modelos en Base.metadata)

config = context.config
# Respetar la URL si el caller ya la seteó (p.ej. el conftest apunta a la base de test);
# solo caer a settings si no vino ninguna. NUNCA pisar la del caller con la de dev.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_settings().LAB_DATABASE_URL)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"),
                      target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}),
                                     prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Autogenerar la migración y agregarle la vista a mano.**

```bash
alembic revision --autogenerate -m "schema inicial"
```
Renombrar el archivo generado a `backend/alembic/versions/0001_schema_inicial.py` (y su `revision = "0001"`, `down_revision = None`). Al final de `upgrade()`, agregar la vista:
```python
    op.execute("""
        CREATE VIEW reel_latest_metrics AS
        SELECT DISTINCT ON (s.reel_id)
            s.reel_id,
            s.captured_at,
            s.snapshot_date,
            s.reach, s.views, s.likes, s.comments, s.saved, s.shares,
            s.total_interactions,
            s.avg_watch_time_ms,
            s.total_watch_time_ms,
            (s.avg_watch_time_ms / 1000.0) AS avg_watch_time_sec,
            (s.total_interactions::float / NULLIF(s.reach, 0)) AS engagement_rate,
            (s.saved::float / NULLIF(s.reach, 0)) AS save_rate,
            (s.shares::float / NULLIF(s.reach, 0)) AS share_rate
        FROM reel_metric_snapshots s
        ORDER BY s.reel_id, s.snapshot_date DESC, s.captured_at DESC;
    """)
```
Y al inicio de `downgrade()`: `op.execute("DROP VIEW IF EXISTS reel_latest_metrics;")`

- [ ] **Step 4: Aplicar la migración a la base de dev.**

Run: `alembic upgrade head`
Expected: crea todas las tablas + la vista, sin error.

- [ ] **Step 5: conftest con DB de test (migraciones + rollback por test).**

`backend/tests/conftest.py`:
```python
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app

TEST_URL = get_settings().LAB_DATABASE_URL_TEST
test_engine = create_engine(TEST_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, join_transaction_mode="create_savepoint"
)


@pytest.fixture(scope="session", autouse=True)
def _migrate_test_db():
    # dropea la vista y todas las tablas del schema public, luego migra desde cero
    with test_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_URL)
    command.upgrade(cfg, "head")
    yield


@pytest.fixture
def db():
    connection = test_engine.connect()
    trans = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    trans.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def _override():
        yield db
    app.dependency_overrides[get_db] = _override
    yield TestClient(app)
    app.dependency_overrides.clear()
```

- [ ] **Step 6: Test de que existan tablas y vista.**

`backend/tests/test_schema.py`:
```python
from sqlalchemy import text


def test_core_tables_and_view_exist(db):
    tables = {r[0] for r in db.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    ))}
    assert {"accounts", "reels", "reel_metric_snapshots", "ingest_runs",
            "angulos", "formatos", "tipos_hook", "categorias", "temas"} <= tables
    views = {r[0] for r in db.execute(text(
        "SELECT table_name FROM information_schema.views WHERE table_schema='public'"
    ))}
    assert "reel_latest_metrics" in views
```

- [ ] **Step 7: Correr los tests (deben pasar).**

Run: `pytest tests/test_schema.py -v`
Expected: PASS.

- [ ] **Step 8: Commit.**

```bash
git add backend/app/models backend/alembic backend/alembic.ini backend/tests/conftest.py backend/tests/test_schema.py
git commit -m "feat(db): modelos + migración inicial (schema completo + vista reel_latest_metrics)"
```

---

### Task 3: Servicio de ingesta (upsert idempotente, sin pisar campos manuales)

**Files:**
- Create: `backend/app/schemas/ingest.py`, `backend/app/repositories/ingest_repository.py`, `backend/app/services/ingest_service.py`, `backend/tests/test_ingest_service.py`

**Interfaces:**
- Consumes: modelos de Task 2; fixture `db`.
- Produces:
  - `IngestBatch`, `IngestReel`, `IngestMetrics` (Pydantic) en `app.schemas.ingest`.
  - `ingest_batch(db, batch: IngestBatch) -> dict` en `app.services.ingest_service`, que devuelve `{"reels_processed": int, "snapshots_written": int}`.

- [ ] **Step 1: Schemas Pydantic del payload.**

`backend/app/schemas/ingest.py`:
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IngestMetrics(BaseModel):
    reach: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    saved: Optional[int] = None
    shares: Optional[int] = None
    total_interactions: Optional[int] = None
    ig_reels_avg_watch_time: Optional[int] = None       # ms
    ig_reels_video_view_total_time: Optional[int] = None  # ms


class IngestReel(BaseModel):
    ig_media_id: str
    permalink: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    media_product_type: Optional[str] = None
    timestamp: Optional[datetime] = None  # published_at
    metrics: IngestMetrics


class IngestAccount(BaseModel):
    ig_user_id: str
    name: str


class IngestBatch(BaseModel):
    account: IngestAccount
    reels: list[IngestReel]
    captured_at: datetime
```

- [ ] **Step 2: Repositorio de upsert.**

`backend/app/repositories/ingest_repository.py`:
```python
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import Account, Reel, ReelMetricSnapshot
from app.schemas.ingest import IngestAccount, IngestReel


def upsert_account(db: Session, data: IngestAccount) -> Account:
    account = db.query(Account).filter(Account.ig_user_id == data.ig_user_id).one_or_none()
    if account is None:
        account = Account(ig_user_id=data.ig_user_id, name=data.name)
        db.add(account)
        db.flush()
    else:
        account.name = data.name
    return account


def upsert_reel(db: Session, account_id: str, data: IngestReel, synced_at: datetime) -> Reel:
    reel = db.query(Reel).filter(Reel.ig_media_id == data.ig_media_id).one_or_none()
    if reel is None:
        reel = Reel(account_id=account_id, ig_media_id=data.ig_media_id)
        db.add(reel)
    # SOLO campos de la API — nunca titulo/guion/labels
    reel.permalink = data.permalink
    reel.caption = data.caption
    reel.thumbnail_url = data.thumbnail_url
    reel.media_product_type = data.media_product_type
    reel.published_at = data.timestamp
    reel.last_synced_at = synced_at
    db.flush()
    return reel


def upsert_snapshot(db: Session, reel: Reel, data: IngestReel, captured_at: datetime) -> bool:
    """Devuelve True si escribió/actualizó un snapshot."""
    snap_date = captured_at.date()
    m = data.metrics
    snap = (db.query(ReelMetricSnapshot)
              .filter(ReelMetricSnapshot.reel_id == reel.id,
                      ReelMetricSnapshot.snapshot_date == snap_date)
              .one_or_none())
    if snap is None:
        snap = ReelMetricSnapshot(reel_id=reel.id, snapshot_date=snap_date)
        db.add(snap)
    snap.captured_at = captured_at
    snap.reach = m.reach
    snap.views = m.views
    snap.likes = m.likes
    snap.comments = m.comments
    snap.saved = m.saved
    snap.shares = m.shares
    snap.total_interactions = m.total_interactions
    snap.avg_watch_time_ms = m.ig_reels_avg_watch_time
    snap.total_watch_time_ms = m.ig_reels_video_view_total_time
    db.flush()
    return True
```

- [ ] **Step 3: Servicio que orquesta el batch.**

`backend/app/services/ingest_service.py`:
```python
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.ingest import IngestBatch
from app.repositories.ingest_repository import upsert_account, upsert_reel, upsert_snapshot


def ingest_batch(db: Session, batch: IngestBatch) -> dict:
    account = upsert_account(db, batch.account)
    account.last_synced_at = batch.captured_at
    reels_processed = 0
    snapshots_written = 0
    for reel_data in batch.reels:
        reel = upsert_reel(db, account.id, reel_data, synced_at=batch.captured_at)
        if upsert_snapshot(db, reel, reel_data, captured_at=batch.captured_at):
            snapshots_written += 1
        reels_processed += 1
    db.commit()
    return {"reels_processed": reels_processed, "snapshots_written": snapshots_written}
```

- [ ] **Step 4: Escribir los tests del servicio.**

`backend/tests/test_ingest_service.py`:
```python
from datetime import datetime, timezone

from app.models import Reel, ReelMetricSnapshot
from app.schemas.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics
from app.services.ingest_service import ingest_batch


def _batch(reach=1000, captured="2026-07-15T06:00:00+00:00"):
    return IngestBatch(
        account=IngestAccount(ig_user_id="ig-1", name="Pleniq"),
        captured_at=datetime.fromisoformat(captured),
        reels=[IngestReel(
            ig_media_id="media-1", permalink="https://ig/1",
            caption="hola", media_product_type="REELS",
            timestamp=datetime(2026, 7, 10, tzinfo=timezone.utc),
            metrics=IngestMetrics(reach=reach, views=5000, likes=300, comments=20,
                                  saved=80, shares=40, total_interactions=440,
                                  ig_reels_avg_watch_time=8200,
                                  ig_reels_video_view_total_time=41000),
        )],
    )


def test_ingest_creates_reel_and_snapshot(db):
    res = ingest_batch(db, _batch())
    assert res == {"reels_processed": 1, "snapshots_written": 1}
    assert db.query(Reel).count() == 1
    assert db.query(ReelMetricSnapshot).count() == 1


def test_ingest_same_day_is_idempotent(db):
    ingest_batch(db, _batch(reach=1000))
    ingest_batch(db, _batch(reach=2500))  # misma media, mismo día
    assert db.query(Reel).count() == 1
    assert db.query(ReelMetricSnapshot).count() == 1  # NO duplica
    snap = db.query(ReelMetricSnapshot).one()
    assert snap.reach == 2500  # actualizó al último valor


def test_ingest_does_not_overwrite_manual_fields(db):
    ingest_batch(db, _batch())
    reel = db.query(Reel).one()
    reel.titulo = "Mi título"
    reel.guion = "Mi guion"
    db.commit()
    ingest_batch(db, _batch(reach=9999))  # re-sync
    reel = db.query(Reel).one()
    assert reel.titulo == "Mi título"  # la ingesta NO lo pisó
    assert reel.guion == "Mi guion"
```

- [ ] **Step 5: Correr los tests (deben pasar).**

Run: `pytest tests/test_ingest_service.py -v`
Expected: PASS (3 tests).

- [ ] **Step 6: Commit.**

```bash
git add backend/app/schemas/ingest.py backend/app/repositories/ingest_repository.py backend/app/services/ingest_service.py backend/tests/test_ingest_service.py
git commit -m "feat(ingest): servicio de upsert idempotente que preserva campos manuales"
```

---

### Task 4: Endpoint `POST /ingest/instagram` con `X-Ingest-Token`

**Files:**
- Create: `backend/app/api/v1/__init__.py`, `backend/app/api/v1/ingest.py`, `backend/tests/test_ingest_api.py`
- Modify: `backend/app/main.py` (incluir router)

**Interfaces:**
- Consumes: `ingest_batch()` (Task 3), `get_db`, `get_settings`.
- Produces: `POST /api/v1/ingest/instagram` → 200 `{"reels_processed", "snapshots_written"}`; 401 si falta/está mal el token.

- [ ] **Step 1: Router de ingesta.**

`backend/app/api/v1/__init__.py`: vacío.
`backend/app/api/v1/ingest.py`:
```python
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.ingest import IngestBatch
from app.services.ingest_service import ingest_batch

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _check_token(x_ingest_token: str | None = Header(default=None)):
    expected = get_settings().LAB_INGEST_TOKEN
    # comparación constant-time para evitar timing side-channel
    if not secrets.compare_digest(x_ingest_token or "", expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token de ingesta inválido")


@router.post("/instagram", status_code=status.HTTP_200_OK, dependencies=[Depends(_check_token)])
def ingest_instagram(batch: IngestBatch, db: Session = Depends(get_db)):
    return ingest_batch(db, batch)
```

- [ ] **Step 2: Registrar el router.**

En `backend/app/main.py`, después de crear `app` y el CORS, agregar:
```python
from app.api.v1.ingest import router as ingest_router

app.include_router(ingest_router, prefix="/api/v1")
```

- [ ] **Step 3: Tests del endpoint.**

`backend/tests/test_ingest_api.py`:
```python
from app.core.config import get_settings

TOKEN = get_settings().LAB_INGEST_TOKEN

PAYLOAD = {
    "account": {"ig_user_id": "ig-1", "name": "Pleniq"},
    "captured_at": "2026-07-15T06:00:00+00:00",
    "reels": [{
        "ig_media_id": "media-1", "permalink": "https://ig/1", "caption": "hola",
        "media_product_type": "REELS", "timestamp": "2026-07-10T12:00:00+00:00",
        "metrics": {"reach": 1000, "views": 5000, "likes": 300, "comments": 20,
                    "saved": 80, "shares": 40, "total_interactions": 440,
                    "ig_reels_avg_watch_time": 8200, "ig_reels_video_view_total_time": 41000},
    }],
}


def test_ingest_requires_token(client):
    resp = client.post("/api/v1/ingest/instagram", json=PAYLOAD)
    assert resp.status_code == 401


def test_ingest_with_token_ok(client):
    resp = client.post("/api/v1/ingest/instagram", json=PAYLOAD,
                       headers={"X-Ingest-Token": TOKEN})
    assert resp.status_code == 200
    assert resp.json() == {"reels_processed": 1, "snapshots_written": 1}
```

- [ ] **Step 4: Correr los tests (deben pasar).**

Run: `pytest tests/test_ingest_api.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit.**

```bash
git add backend/app/api backend/app/main.py backend/tests/test_ingest_api.py
git commit -m "feat(api): POST /ingest/instagram con guard X-Ingest-Token"
```

---

### Task 5: Lectura `GET /reels` (vista de últimas métricas + ratios)

**Files:**
- Create: `backend/app/schemas/reel.py`, `backend/app/repositories/reel_repository.py`, `backend/app/services/reel_service.py`, `backend/app/api/v1/reels.py`, `backend/tests/test_reels_api.py`
- Modify: `backend/app/main.py` (incluir router)

**Interfaces:**
- Consumes: vista `reel_latest_metrics`, modelos, `ingest_batch` (para armar datos en el test).
- Produces:
  - `ReelRow` (Pydantic) en `app.schemas.reel`.
  - `list_reels_with_latest(db) -> list[dict]` en `app.repositories.reel_repository`.
  - `GET /api/v1/reels` → `list[ReelRow]`.

- [ ] **Step 1: Schema del read model.**

`backend/app/schemas/reel.py`:
```python
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel


class ReelRow(BaseModel):
    id: str
    ig_media_id: str
    permalink: Optional[str] = None
    caption: Optional[str] = None
    thumbnail_url: Optional[str] = None
    titulo: Optional[str] = None
    published_at: Optional[datetime] = None
    snapshot_date: Optional[date] = None
    reach: Optional[int] = None
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    saved: Optional[int] = None
    shares: Optional[int] = None
    total_interactions: Optional[int] = None
    avg_watch_time_sec: Optional[float] = None
    engagement_rate: Optional[float] = None
    save_rate: Optional[float] = None
    share_rate: Optional[float] = None
```

- [ ] **Step 2: Repositorio de lectura (join reels + vista).**

`backend/app/repositories/reel_repository.py`:
```python
from sqlalchemy import text
from sqlalchemy.orm import Session


def list_reels_with_latest(db: Session) -> list[dict]:
    rows = db.execute(text("""
        SELECT r.id, r.ig_media_id, r.permalink, r.caption, r.thumbnail_url,
               r.titulo, r.published_at,
               m.snapshot_date, m.reach, m.views, m.likes, m.comments, m.saved,
               m.shares, m.total_interactions, m.avg_watch_time_sec,
               m.engagement_rate, m.save_rate, m.share_rate
        FROM reels r
        LEFT JOIN reel_latest_metrics m ON m.reel_id = r.id
        ORDER BY r.published_at DESC NULLS LAST
    """)).mappings().all()
    return [dict(row) for row in rows]
```

- [ ] **Step 3: Servicio + router.**

`backend/app/services/reel_service.py`:
```python
from sqlalchemy.orm import Session
from app.repositories.reel_repository import list_reels_with_latest
from app.schemas.reel import ReelRow


def get_reels(db: Session) -> list[ReelRow]:
    return [ReelRow(**row) for row in list_reels_with_latest(db)]
```

`backend/app/api/v1/reels.py`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.reel import ReelRow
from app.services.reel_service import get_reels

router = APIRouter(prefix="/reels", tags=["reels"])


@router.get("", response_model=list[ReelRow])
def list_reels(db: Session = Depends(get_db)):
    return get_reels(db)
```

En `backend/app/main.py`:
```python
from app.api.v1.reels import router as reels_router

app.include_router(reels_router, prefix="/api/v1")
```

- [ ] **Step 4: Test del endpoint.**

`backend/tests/test_reels_api.py`:
```python
from datetime import datetime, timezone
from app.schemas.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics
from app.services.ingest_service import ingest_batch


def test_reels_returns_latest_metrics_and_ratios(client, db):
    ingest_batch(db, IngestBatch(
        account=IngestAccount(ig_user_id="ig-1", name="Pleniq"),
        captured_at=datetime(2026, 7, 15, 6, tzinfo=timezone.utc),
        reels=[IngestReel(ig_media_id="media-1", media_product_type="REELS",
                          timestamp=datetime(2026, 7, 10, tzinfo=timezone.utc),
                          metrics=IngestMetrics(reach=1000, views=5000, likes=300,
                                                comments=20, saved=80, shares=40,
                                                total_interactions=440,
                                                ig_reels_avg_watch_time=8200,
                                                ig_reels_video_view_total_time=41000))],
    ))
    resp = client.get("/api/v1/reels")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    row = data[0]
    assert row["reach"] == 1000
    assert row["engagement_rate"] == 0.44   # 440/1000
    assert row["save_rate"] == 0.08         # 80/1000
    assert abs(row["avg_watch_time_sec"] - 8.2) < 1e-6
```

- [ ] **Step 5: Correr los tests (deben pasar).**

Run: `pytest tests/test_reels_api.py -v`
Expected: PASS.

- [ ] **Step 6: Correr toda la suite.**

Run: `pytest -v`
Expected: todos PASS.

- [ ] **Step 7: Commit.**

```bash
git add backend/app/schemas/reel.py backend/app/repositories/reel_repository.py backend/app/services/reel_service.py backend/app/api/v1/reels.py backend/app/main.py backend/tests/test_reels_api.py
git commit -m "feat(api): GET /reels con últimas métricas y ratios desde la vista"
```

---

### Task 6: Seed mock (datos de ejemplo para ver el pipe funcionando)

**Files:**
- Create: `backend/app/seed_mock.py`

**Interfaces:**
- Consumes: `ingest_batch()`, `SessionLocal`.

- [ ] **Step 1: Script de seed con 3 reels mock.**

`backend/app/seed_mock.py`:
```python
"""Carga 3 reels mock vía el servicio de ingesta. Uso: python -m app.seed_mock"""
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.schemas.ingest import IngestBatch, IngestAccount, IngestReel, IngestMetrics


def main():
    now = datetime.now(timezone.utc)
    batch = IngestBatch(
        account=IngestAccount(ig_user_id="ig-demo", name="Cuenta Demo"),
        captured_at=now,
        reels=[
            IngestReel(ig_media_id=f"media-{i}", permalink=f"https://instagram.com/reel/{i}",
                       caption=f"Reel de ejemplo {i}", media_product_type="REELS",
                       timestamp=datetime(2026, 7, i + 1, tzinfo=timezone.utc),
                       metrics=IngestMetrics(reach=1000 * i, views=5000 * i, likes=300 * i,
                                             comments=20 * i, saved=80 * i, shares=40 * i,
                                             total_interactions=440 * i,
                                             ig_reels_avg_watch_time=8000 + 200 * i,
                                             ig_reels_video_view_total_time=40000 + 1000 * i))
            for i in range(1, 4)
        ],
    )
    from app.services.ingest_service import ingest_batch
    db = SessionLocal()
    try:
        res = ingest_batch(db, batch)
        print(f"Seed OK: {res}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Correr el seed contra la base de dev.**

Run: `cd backend && source .venv/bin/activate && python -m app.seed_mock`
Expected: `Seed OK: {'reels_processed': 3, 'snapshots_written': 3}`

- [ ] **Step 3: Verificar el endpoint a mano.**

Run (en otra terminal, con el server levantado `uvicorn app.main:app --reload`):
`curl -s http://localhost:8000/api/v1/reels | python -m json.tool`
Expected: 3 reels con métricas y ratios.

- [ ] **Step 4: Commit.**

```bash
git add backend/app/seed_mock.py
git commit -m "chore(seed): script de datos mock para el walking skeleton"
```

---

### Task 7: Frontend — tabla que consume `GET /reels`

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/lib/api.ts`, `frontend/src/styles.css`

**Interfaces:**
- Consumes: `GET /api/v1/reels` (proxy de Vite a `localhost:8000`).

- [ ] **Step 1: package.json + config Vite (con proxy al backend).**

`frontend/package.json`:
```json
{
  "name": "laboratorio-contenido-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": { "dev": "vite", "build": "vite build", "preview": "vite preview" },
  "dependencies": { "react": "^18.3.1", "react-dom": "^18.3.1" },
  "devDependencies": {
    "@types/react": "^18.3.12", "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4", "typescript": "^5.6.3", "vite": "^6.0.7"
  }
}
```

`frontend/vite.config.ts`:
```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
```

`frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020", "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"], "module": "ESNext",
    "skipLibCheck": true, "moduleResolution": "bundler",
    "jsx": "react-jsx", "strict": true, "noEmit": true
  },
  "include": ["src"]
}
```

`frontend/index.html`:
```html
<!doctype html>
<html lang="es">
  <head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Laboratorio de Contenido</title></head>
  <body><div id="root"></div><script type="module" src="/src/main.tsx"></script></body>
</html>
```

- [ ] **Step 2: Cliente API + entrypoint + estilos.**

`frontend/src/lib/api.ts`:
```ts
export interface ReelRow {
  id: string; ig_media_id: string; titulo: string | null; caption: string | null;
  permalink: string | null; published_at: string | null;
  reach: number | null; views: number | null; likes: number | null;
  comments: number | null; saved: number | null; shares: number | null;
  total_interactions: number | null; avg_watch_time_sec: number | null;
  engagement_rate: number | null; save_rate: number | null; share_rate: number | null;
}

export async function fetchReels(): Promise<ReelRow[]> {
  const res = await fetch("/api/v1/reels");
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}
```

`frontend/src/main.tsx`:
```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><App /></React.StrictMode>
);
```

`frontend/src/styles.css`:
```css
body { font-family: system-ui, sans-serif; margin: 0; background: #fafafa; color: #111; }
.wrap { max-width: 1200px; margin: 0 auto; padding: 24px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { border-bottom: 1px solid #eee; padding: 8px 10px; text-align: right; white-space: nowrap; }
th:first-child, td:first-child { text-align: left; }
th { background: #f4f4f5; position: sticky; top: 0; }
```

- [ ] **Step 3: Componente App con la tabla.**

`frontend/src/App.tsx`:
```tsx
import { useEffect, useState } from "react";
import { fetchReels, ReelRow } from "./lib/api";

const pct = (v: number | null) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const num = (v: number | null) => (v == null ? "—" : v.toLocaleString("es-AR"));

export default function App() {
  const [reels, setReels] = useState<ReelRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchReels().then(setReels).catch((e) => setError(e.message)); }, []);

  return (
    <div className="wrap">
      <h1>Laboratorio de Contenido</h1>
      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
      <table>
        <thead><tr>
          <th>Título / Caption</th><th>Publicado</th><th>Reach</th><th>Views</th>
          <th>Likes</th><th>Coment.</th><th>Saves</th><th>Shares</th>
          <th>ER</th><th>Save%</th><th>Share%</th><th>Watch (s)</th>
        </tr></thead>
        <tbody>
          {reels.map((r) => (
            <tr key={r.id}>
              <td>{r.titulo || r.caption || r.ig_media_id}</td>
              <td>{r.published_at ? r.published_at.slice(0, 10) : "—"}</td>
              <td>{num(r.reach)}</td><td>{num(r.views)}</td><td>{num(r.likes)}</td>
              <td>{num(r.comments)}</td><td>{num(r.saved)}</td><td>{num(r.shares)}</td>
              <td>{pct(r.engagement_rate)}</td><td>{pct(r.save_rate)}</td>
              <td>{pct(r.share_rate)}</td>
              <td>{r.avg_watch_time_sec == null ? "—" : r.avg_watch_time_sec.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: Instalar y levantar el front.**

```bash
cd frontend && npm install && npm run dev
```
Expected: Vite sirve en `http://localhost:5173`.

- [ ] **Step 5: Verificar en el navegador.**

Con el backend levantado (`uvicorn app.main:app --reload` en `backend/`) y el seed corrido, abrir `http://localhost:5173`.
Expected: se ven los 3 reels mock con métricas y ratios.

- [ ] **Step 6: Commit.**

```bash
git add frontend
git commit -m "feat(frontend): tabla de reels que consume GET /reels (walking skeleton)"
```

---

### Task 8: Verificación end-to-end + README + push

**Files:**
- Create: `README.md`

- [ ] **Step 1: Correr toda la suite backend.**

Run: `cd backend && source .venv/bin/activate && pytest -v`
Expected: todos PASS.

- [ ] **Step 2: Verificación manual end-to-end (guion).**
  1. `brew services list` → postgresql@16 `started`.
  2. Backend: `uvicorn app.main:app --reload` → `GET /health` = 200.
  3. `python -m app.seed_mock` → 3 reels.
  4. Front: `npm run dev` → tabla con 3 reels y ratios correctos (ER del reel 1 = 44.0%).

- [ ] **Step 3: README con cómo correr.**

`README.md`:
```markdown
# Laboratorio de Contenido

Dashboard interno de métricas de Reels de Instagram. Ver `BLUEPRINT.md` y `docs/superpowers/`.

## Correr local (Iteración 1)
1. Postgres: `brew services start postgresql@16` (bases `laboratorio_contenido` y `_test`).
2. Backend: `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
3. Seed demo: `python -m app.seed_mock`
4. Front: `cd frontend && npm run dev` → http://localhost:5173
5. Tests: `cd backend && pytest -v`
```

- [ ] **Step 4: Commit y push.**

```bash
git add README.md
git commit -m "docs: README con instrucciones de la Iteración 1"
git push
```

---

## Self-Review (hecho)

**Cobertura del spec (Iteración 1):** DB con schema completo + vista (Task 2) ✓ · ingesta idempotente que preserva campos manuales (Task 3) ✓ · endpoint de ingesta con token (Task 4) ✓ · lectura con ratios y watch time en segundos (Task 5) ✓ · front tabla (Task 7) ✓. Fuera de esta iteración (por diseño iterativo, con su propio plan): sync on-demand/liveness/n8n (Iter 2), etiquetado/análisis (Iter 3), export/detalle (Iter 4).

**Placeholders:** ninguno; todo el código está completo.

**Consistencia de tipos:** `IngestBatch/IngestReel/IngestMetrics` definidos en Task 3 y usados igual en Tasks 4-6. `ReelRow` definido en Task 5 y consumido por el front en Task 7 con los mismos campos. `ingest_batch()` devuelve `{"reels_processed","snapshots_written"}` en Task 3 y se asume ese shape en Tasks 4-6. Nombres de métricas alineados con el spec (`views`, `saved`, `ig_reels_avg_watch_time`, etc.).

---

## Resolución de hallazgos del review (2026-07-15)

Aplicado en fases, de más a menos importante:

**Fase 1 — Critical**
- **C1** ✅ `alembic/env.py` ya no pisa la URL: solo cae a settings si el caller no la seteó → el conftest puede apuntar a la base de test sin migrar la de dev.

**Fase 2 — Important**
- **I1** ✅ `conftest.py` usa `join_transaction_mode="create_savepoint"` → el `commit()` del service cierra un savepoint, no la transacción externa; el rollback por test aísla de verdad (sin fugas ni violaciones de UNIQUE entre tests).
- **I2** ✅ Timestamps con `_now()` (tz-aware, `datetime.now(timezone.utc)`) en vez de `datetime.utcnow` (naive + deprecado en Python 3.12+).

**Fase 3 — Suggestions**
- **S1** ✅ Token de ingesta con `secrets.compare_digest` (constant-time).
- **S2** ✅ `POST /ingest/instagram` responde `200` (trabajo sincrónico); el `202` queda reservado para `POST /sync/refresh` (Iter 2, async).
- **S5** ✅ CORS con `allow_credentials=False` (v1 sin auth; `*` + credentials era combo inválido).
- **S3** 🔵 Decisión: se mantiene `commit()` en el service por consistencia con el patrón de PLENIQ; el aislamiento de tests ya lo resuelve I1. Migrar a unit-of-work en el endpoint queda como refactor acotado a futuro.
- **S4** 🔵 Diferido (YAGNI): el N+1 de `ingest_batch` (2 queries/reel) es sano para un sync diario/manual de decenas-cientos de reels. Si escala, pre-cargar reels por `ig_media_id` en una sola query.
- **S6** 🔵 Checkpoint: verificar el mixin `_LabelBase` en el primer `alembic revision --autogenerate` (Task 2, Step 3); si algo no copia bien las columnas, se explicitan las 5 tablas sin mixin.
