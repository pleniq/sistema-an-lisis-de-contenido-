# Laboratorio de Contenido

Dashboard interno que jala **solo métricas** de los Reels de Instagram (Graph API oficial, nada de screenshots), permite **etiquetar** cada reel por ángulo/formato/hook/categoría/tema, muestra **objetivamente qué tipo de contenido promedia mejores números**, y **exporta** la data lista para pegar en Claude Code y planificar la semana siguiente.

- Documento maestro: [`BLUEPRINT.md`](BLUEPRINT.md)
- Diseño técnico: [`docs/superpowers/specs/2026-07-15-laboratorio-contenido-design.md`](docs/superpowers/specs/2026-07-15-laboratorio-contenido-design.md)
- Plan de implementación: [`docs/superpowers/plans/`](docs/superpowers/plans/)

## Arquitectura

```
Front (React+Vite, :5173)  ──proxy /api──►  Backend (FastAPI, :8010)  ──►  PostgreSQL 16
                                                   ▲
                                                   │ POST /ingest/instagram (X-Ingest-Token)
                                            n8n (webhooks) ──► Graph API de Meta
```

- **Backend**: FastAPI en 3 capas (`models / repositories / services / api`) + Alembic + SQLAlchemy 2.0. Toda la lógica testeable en Python.
- **DB**: Postgres con snapshot diario por reel (idempotente) + vista `reel_latest_metrics` (últimas métricas + ratios).
- **n8n**: pega a la Graph API y postea el batch al backend. Workflows importables en [`n8n/`](n8n/).
- **Sync on-demand**: se actualiza cuando abrís el sistema (si está viejo) o con el botón, con 3 guardas (frescura / lock / liveness de n8n). No hay cron porque corre local y la máquina no está siempre prendida.

> **Puertos:** el backend corre en **8010** (el 8000 lo usa otro proyecto local). El proxy de Vite ya apunta a 8010.

## Requisitos

- PostgreSQL 16 (`brew install postgresql@16 && brew services start postgresql@16`)
- Python 3.13 · Node 20+
- Bases: `laboratorio_contenido` y `laboratorio_contenido_test` (`createdb ...`)

## Correr local

**Backend**
```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                 # crea schema + vista + índices
uvicorn app.main:app --port 8010 --reload
```

**Datos de ejemplo** (sin n8n todavía)
```bash
cd backend && source .venv/bin/activate
python -m app.seed_mock              # 3 reels mock
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

**Tests** (33, contra la base de test)
```bash
cd backend && source .venv/bin/activate && pytest -q
```

## Endpoints (`/api/v1`)

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/ingest/instagram` | Recibe el batch de n8n (`X-Ingest-Token`). Upsert + snapshot idempotente. Nunca pisa `titulo`/`guion`/etiquetas. |
| GET | `/sync/status` | `{ n8n_alive, running, last_synced_at, last_run }` para el indicador. |
| POST | `/sync/refresh?force=&trigger=` | Dispara el sync con las 3 guardas → 202 / 409 / 503 / 200. |
| GET | `/reels` | Tabla: reels + etiquetas + últimas métricas + ratios. |
| GET | `/reels/{id}` | Detalle de un reel. |
| GET | `/reels/{id}/history` | Historial de snapshots (curva en el tiempo). |
| PATCH | `/reels/{id}` | Edita `titulo`/`guion` y las 5 dimensiones (crea la etiqueta al vuelo). |
| POST | `/reels/export` | Markdown compacto de los reels elegidos, para pegar en Claude Code. |
| GET/POST | `/labels/{dimension}` | Lista / crea valores de una dimensión (`angulo`,`formato`,`tipo_hook`,`categoria`,`tema`). |
| GET | `/analysis?group_by=` | **Qué funciona:** promedio de cada métrica + ratios por grupo + count. |
| GET | `/health` | Health check. |

## Etapa 0 — Setup Meta/IG + n8n (lo hacés vos, ~1h, una vez)

El software está listo y anda con datos mock. Para traer métricas **reales** falta el setup que requiere tus credenciales:

1. Instalar n8n local e importar los workflows de [`n8n/`](n8n/) (ver [`n8n/README.md`](n8n/README.md)).
2. Vincular IG ↔ Página de FB · crear la app en Meta · generar el long-lived token · guardarlo en la credencial de n8n.
3. Completar en `backend/.env`: `LAB_N8N_PING_WEBHOOK_URL` y `LAB_N8N_INGEST_WEBHOOK_URL`.

Con eso, `/sync/status` pasa a `n8n_alive: true` y el botón "Actualizar" dispara la ingesta real.

## Estado

| Iteración | Qué | Estado |
|---|---|---|
| 1 | Walking skeleton: DB + ingesta + `/reels` + tabla | ✅ |
| 2 | Sync on-demand (frescura/lock/liveness) + workflows n8n + UI | ✅ |
| 3 | Etiquetado + labels API + análisis "qué funciona" | ✅ |
| 4 | Export a Claude + detalle + historial | ✅ |
| 5 | Refresh de token n8n + índices de hardening | ✅ |
| 0 | Setup Meta/IG + n8n con token real | ⏳ (lo hacés vos) |

## Límites honestos (v1)

- **Snapshot on-demand ≠ diario garantizado:** hay foto los días que abrís/actualizás. Diario garantizado → VPS always-on (v2).
- **Sin duración de video ni curva de retención** por la API → solo watch time promedio en segundos; el detalle linkea al permalink para mirar el resto a mano.
- `impressions` deprecado → se usa `reach`. `plays` renombrado a `views`.
