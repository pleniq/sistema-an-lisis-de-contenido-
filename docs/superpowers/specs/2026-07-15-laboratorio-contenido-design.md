# Laboratorio de Contenido — Diseño (v1)

- **Fecha:** 2026-07-15
- **Autor:** Luca + Claude
- **Estado:** Aprobado para escribir plan de implementación
- **Stack obligatorio:** FastAPI + PostgreSQL + Alembic + SQLAlchemy 2.0 + Pydantic 2 · n8n · React + Vite

---

## 1. Objetivo

Dashboard interno ("laboratorio de contenido") que jala **solo métricas** de cada Reel de Instagram desde la Graph API oficial (nada de screenshots), permite **etiquetar** cada Reel por ángulo/formato/hook/categoría/tema, y muestra **objetivamente qué tipo de contenido promedia mejores números**. Uso interno mío hoy; activo reutilizable para clientes a futuro.

Los guiones **no** se automatizan (ahí está mi criterio y voz). Lo que se automatiza es **jalar y comparar métricas**.

Además, el sistema **exporta** la data (título + guion + formato + etiquetas + stats) de uno o varios reels seleccionados en un formato compacto token-eficiente, para pegar en Claude Code y planificar el contenido de la semana siguiente con la data real de rendimiento. El dashboard es la capa de datos; Claude Code, con ese export, es la capa de análisis y creación.

## 2. Alcance

**v1 (este spec):** ingesta on-demand vía n8n + Postgres con snapshots + dashboard (tabla ordenable + etiquetado + vista "qué funciona" + detalle con historial) + **export multi-select a Claude Code**.

**v2 (fuera de este spec):** etiquetado asistido por IA (sugerir formato/categoría leyendo el caption), selector multi-cuenta, vista "primeras 48h", deploy always-on (VPS) con snapshots diarios garantizados.

## 3. Decisiones tomadas

| # | Decisión | Elegido |
|---|---|---|
| 1 | Dónde vive la lógica de ingesta | **n8n → endpoint FastAPI.** n8n orquesta (API, token, retries), el backend hace upsert/snapshot/ratios en Python testeable |
| 2 | Dónde vive el token long-lived | **Credencial de n8n** (cifrada). `accounts.token_ref` guarda solo un label, nunca el secreto |
| 3 | Auth del dashboard en v1 | **Sin login de usuario** (corre local). El endpoint de ingesta igual lleva `X-Ingest-Token` máquina-a-máquina |
| 4 | Quién pega a la Graph API | **n8n** (paginación, retries/backoff, refresh de token visual; reutilizable para clientes) |
| 5 | Modelo de disparo | **On-demand** (auto al abrir + botón manual), NO cron 6am — ver §5 |
| 6 | Etiquetas | **Una tabla de dimensión por dimensión** + FK nullable en `reels` (SQL-first, GROUP BY limpio) |

### Por qué NO cron 6am (contexto local)
Un Schedule Trigger de n8n solo dispara mientras n8n está corriendo. Todo esto corre local: la máquina está apagada la mayor parte del tiempo. Un cron a las 6am con la máquina dormida **no se ejecuta ni se acumula** — el disparo se pierde en silencio, y con él el snapshot de ese día (lo único irrecuperable). Por eso el disparo correcto para una herramienta local es **"cuando la uso"**.

## 4. Métricas verificadas (Graph API, doc oficial Meta — verificado 2026-07-15)

`field names` EXACTOS para media tipo Reel en `GET /{ig-media-id}/insights`:

| Concepto | Nombre EXACTO API | Columna DB | Unidad / nota |
|---|---|---|---|
| Alcance | `reach` | `reach` | usuarios únicos |
| Reproducciones/plays | `views` | `views` | ⚠️ `plays` fue renombrado a `views` |
| Likes | `likes` | `likes` | count |
| Comentarios | `comments` | `comments` | count |
| Guardados | `saved` | `saved` | count |
| Compartidos | `shares` | `shares` | count |
| Interacciones totales | `total_interactions` | `total_interactions` | likes+saves+comments+shares (menos removidos) |
| Watch time promedio | `ig_reels_avg_watch_time` | `avg_watch_time_ms` | **milisegundos** → seg en capa de lectura |
| Watch time total | `ig_reels_video_view_total_time` | `total_watch_time_ms` | **milisegundos**, incluye replays |

**Reglas duras:**
- `impressions` está **deprecado** para contenido creado después del 2-jul-2024 → no se usa; se usa `reach`.
- **Duración del video NO viene** por la API de insights → nada de "retención %"; solo watch time en segundos.
- Los dos watch times vienen en **ms** → se guardan crudos en ms (dato fiel) y se exponen segundos en la capa de lectura.
- Listar solo Reels: `GET /{ig-user-id}/media?fields=id,media_type,media_product_type,permalink,caption,thumbnail_url,timestamp` y filtrar `media_product_type == "REELS"`.
- Permisos: `instagram_basic`, `instagram_manage_insights`, `pages_show_list`/`pages_read_engagement` (camino FB-Page).

**Fuentes:**
- https://developers.facebook.com/docs/instagram-platform/reference/instagram-media/insights/
- https://docs.supermetrics.com/docs/instagram-insights-updates

## 5. Modelo de disparo on-demand (el cambio central)

Disparo = **cuando abro el sistema + botón manual**, con 3 guardas:

1. **Guarda de frescura ("entrar sin actualizar"):** si el último sync fue hace `< LAB_SYNC_STALE_MINUTES` (default 5) → no dispara, entra con lo que hay.
2. **Run-lock + indicador:** el estado vive en `ingest_runs`. Si ya hay una corrida `running`, un nuevo disparo responde 409 "ya corriendo" y no dispara otra. El front muestra indicador y deshabilita el botón. Un run `running` colgado > `LAB_SYNC_STUCK_MINUTES` (default 10) se considera muerto → se marca `error` y se permite uno nuevo (no se wedgea).
3. **Liveness de n8n:** antes de disparar el ingest real, el backend pega a un **webhook de ping** de n8n (timeout corto ~2s). Si 200 → n8n vivo y la ruta de webhooks activa → dispara ingest. Si timeout/error → 503 "n8n apagado", el front lo muestra.

### Flujo
```
POST /api/v1/sync/refresh   (auto-al-abrir si stale, o botón)
  1. ¿run 'running' vigente? → sí: 409 "ya corriendo"          [lock]
  2. GET ping webhook n8n → ¿200? → no: 503 "n8n apagado"       [liveness]
  3. crea ingest_run(status=running); dispara webhook ingest de n8n; responde 202
        → n8n: GET media (paginado) + insights por reel (retries/backoff, token de credencial)
        → n8n: POST /api/v1/ingest/instagram  (batch + X-Ingest-Token)
        → backend: upsert reels + snapshot del día + cierra ingest_run(status=ok)

GET /api/v1/sync/status → { n8n_alive, running, last_synced_at, last_run }
   El front lo pollea para el indicador y el estado del botón.
```
Async (dispara + pollea estado), no una sola llamada sincrónica larga: con muchos reels una llamada sincrónica timeoutea, y el async es lo que hace que el indicador de "corriendo" tenga sentido.

### Comportamiento del front al abrir
- `GET /sync/status`.
- Si `n8n_alive && !running && (now - last_synced_at) > stale` → auto `POST /sync/refresh`, pollea hasta `done`, muestra datos.
- Si no → carga los datos que hay ("entrar sin actualizar"). Si `!n8n_alive`, muestra chip "n8n apagado" y deshabilita el botón.
- Botón "Actualizar" siempre disponible (salvo mientras corre).

## 6. Modelo de datos (PostgreSQL + Alembic)

Prefijo de env: `LAB_`. IDs `String(36)` UUID (patrón PLENIQ). SQLAlchemy 2.0 `Mapped`/`mapped_column`.

### `accounts` (multi-cuenta desde día 1)
`id` PK · `ig_user_id` UNIQUE · `name` · `token_ref` (label a credencial n8n, **nunca el secreto**) · `last_synced_at` · `created_at` · `updated_at`

### `reels` (una fila por reel; acá viven las etiquetas y mis textos)
`id` PK · `account_id` FK→accounts · `ig_media_id` **UNIQUE** (clave de dedupe) · `permalink` · `caption` (text null, viene de IG) · `thumbnail_url` (text null) · `media_product_type` · `published_at` · `first_seen_at` · `last_synced_at` · `created_at` · `updated_at`
Campos manuales míos (nullable, editables desde el front, **la ingesta nunca los pisa**): `titulo` · `guion` (text)
FKs de etiqueta (nullable): `angulo_id` · `formato_id` · `tipo_hook_id` · `categoria_id` · `tema_id`

### Tablas de dimensión (valores abiertos al vuelo)
`angulos`, `formatos`, `tipos_hook`, `categorias`, `temas` — cada una:
`id` PK · `account_id` FK→accounts · `name` · UNIQUE(`account_id`,`name`) · `created_at`
`categorias` se siembra con TOFU/MOFU/BOFU pero queda abierta. Crear valor nuevo = INSERT (frecuente). Sumar dimensión nueva = migración (raro).

### `reel_metric_snapshots` (una fila por reel por día)
`id` PK · `reel_id` FK→reels · `captured_at` (timestamptz) · `snapshot_date` (date) · `reach` · `views` · `likes` · `comments` · `saved` · `shares` · `total_interactions` · `avg_watch_time_ms` (bigint) · `total_watch_time_ms` (bigint) · `created_at`
**UNIQUE(`reel_id`, `snapshot_date`)** → idempotente: correr de nuevo el mismo día **actualiza** esa fila. Métricas nullable.

### `ingest_runs` (log por corrida + lock)
`id` PK · `account_id` FK · `trigger` (`auto`|`manual`) · `status` (`running`|`ok`|`partial`|`error`) · `started_at` · `finished_at` · `reels_processed` · `snapshots_written` · `error_detail` (text null)

### Vista `reel_latest_metrics`
Último snapshot por reel (`DISTINCT ON (reel_id) … ORDER BY reel_id, snapshot_date DESC`) + ratios con `NULLIF(reach,0)`:
- `engagement_rate = total_interactions / reach`
- `save_rate = saved / reach`
- `share_rate = shares / reach`
- `avg_watch_time_sec = avg_watch_time_ms / 1000.0`

## 7. Backend FastAPI (3 capas, patrón PLENIQ)

`app/{core,models,schemas,repositories,services,api/v1}` · `main.py` · CORS abierto en local · routers con prefijo `/api/v1`.

| Endpoint | Qué hace |
|---|---|
| `POST /ingest/instagram` | Recibe batch de n8n (`X-Ingest-Token`). Upsert account/reels/snapshot + cierra run, en transacción. Idempotente. Re-sincroniza **todos** los reels (DB = espejo de IG). Solo toca campos de la API; **nunca pisa** `titulo`/`guion`/etiquetas. |
| `POST /sync/refresh` | Dispara sync on-demand con las 3 guardas (lock, liveness, frescura). Responde 202 / 409 / 503. |
| `GET /sync/status` | `{ n8n_alive, running, last_synced_at, last_run }` para el indicador. |
| `GET /reels` | Tabla: reels + últimas métricas + ratios. Filtros por dimensión y fecha; sort por cualquier columna. |
| `GET /reels/{id}` | Detalle + historial de snapshots (curva en el tiempo). |
| `PATCH /reels/{id}` | Edita mis campos manuales: `titulo`, `guion` y las 5 dimensiones; crea valor de etiqueta al vuelo si el `name` no existe. |
| `GET/POST /labels/{dimension}` | Lista / crea valores de una dimensión. |
| `GET /analysis?group_by=angulo\|formato\|categoria\|tipo_hook\|tema` | **El corazón:** promedio de cada métrica + ratios por grupo + cantidad de reels. |
| `POST /reels/export` | Devuelve texto compacto (markdown) listo para pegar en Claude Code, para 1 o varios reels seleccionados. Ver formato abajo. |
| `GET /accounts`, `GET /ingest/runs`, `GET /health` | Estado y observabilidad. |

### Export para Claude Code (formato token-eficiente)
`POST /reels/export` body `{ "reel_ids": [...] }` → `{ "format":"markdown", "reels": N, "text":"..." }`. El front copia `text` al portapapeles. La lógica de formato vive en el backend (una sola fuente, testeable).

El texto se arma en **markdown** (elegido por ser lo que menos tokens gasta sin perder estructura que el LLM entienda) en dos partes:
1. **Tabla de stats** — una fila por reel, headers compartidos una sola vez: `# · título · publicado · ángulo · formato · hook · categoría · tema · reach · views · likes · comments · saves · shares · ER · save% · share% · watch_s`. Números **enteros crudos** (sin abreviar tipo "12k", para no perder precisión); ratios a 3 decimales.
2. **Sección Guiones** — un subbloque por reel (`### N — título`, permalink y el guion completo debajo). Separa el texto largo de la tabla numérica para no repetir headers ni inflar tokens.

Así, al decirle a Claude "analizá el contenido que subí y armá la semana que viene", ya tiene título + guion + formato + etiquetas + todas las stats y cómo viene rindiendo cada pieza, en el mínimo de tokens.

**Seguridad:** "sin auth v1" = sin login de usuario. El endpoint de ingesta (que escribe) valida `X-Ingest-Token` (env `LAB_INGEST_TOKEN`). Lectura abierta en local. Al exponer, se agrega el login OTP de PLENIQ sin tocar el modelo.

**Config (`LAB_` env):** `LAB_DATABASE_URL`, `LAB_INGEST_TOKEN`, `LAB_N8N_PING_WEBHOOK_URL`, `LAB_N8N_INGEST_WEBHOOK_URL`, `LAB_SYNC_STALE_MINUTES=5`, `LAB_SYNC_STUCK_MINUTES=10`.

**Tests:** idempotencia del upsert (correr 2x mismo día = 1 snapshot actualizado), cálculo de ratios (incl. `reach=0` → null, no división por cero), lock (segundo refresh mientras corre → 409), liveness (ping down → 503), que la ingesta **no pise** `titulo`/`guion`/etiquetas, y formato de export estable.

## 8. Ingesta n8n (2 workflows)

1. **Ping** (Webhook `GET`): responde 200 inmediato. Es la primera instancia que valida que n8n está vivo y la ruta de webhooks activa.
2. **Ingest** (Webhook, disparado por el backend): GET `/{ig-user-id}/media` (paginado) → filtro `media_product_type=REELS` → loop GET insights con los 9 fields de §4 → arma batch → POST `/api/v1/ingest/instagram` con `X-Ingest-Token`. Maneja: token vencido (alerta), rate limit (retry con backoff).
3. **Refresh token** (Schedule ~cada 50 días, corre cuando n8n está prendido): renueva el long-lived token.
   ⚠️ **Wrinkle a validar en Etapa 3:** actualizar una credencial de n8n desde un workflow requiere la **API pública de n8n** (PATCH a la credencial por ID). Si no cierra, fallback = guardar el token en un secreto que el workflow lea. Se valida al armar el workflow.

Prerequisito: **n8n instalado local** (lo instala Luca antes de Etapa 3).

## 9. Frontend (React + Vite + react-router, estilo NUSA)

- **Tabla principal:** thumbnail + todas las métricas + ratios, ordenable por cualquier columna, filtros por dimensión y fecha. Densa.
- **Etiquetado rápido:** click en un reel → editar `titulo` y `guion` + dropdowns inline para las 5 dimensiones con create-on-the-fly (~10 seg/reel, una vez).
- **Vista "qué funciona":** selector de group-by → tabla de promedios por grupo + count.
- **Detalle de reel:** permalink a IG + thumbnail + mini-gráfico de historial de snapshots.
- **Selección múltiple + "Copiar para Claude":** checkboxes en la tabla para elegir 1 o varios reels → botón que pega a `POST /reels/export` y copia el texto al portapapeles (`navigator.clipboard`). Es el input para que Claude Code arme la semana siguiente con la data real.
- **Sync UI:** botón "Actualizar" + indicador de estado (idle / corriendo / n8n apagado), auto-refresh al abrir si stale. Pollea `GET /sync/status`.
- `src/lib/api.ts` como en NUSA.

## 10. Plan por etapas

- **Etapa 0 — Setup Meta/IG + instalar n8n** (guiado, 1 vez, ~1h, sin código): instalar n8n local · vincular IG↔Página FB · app en Meta · long-lived token · guardarlo en credencial n8n · validar permisos y (si hace falta) App Review.
- **Etapa 1 — DB + Alembic:** schema completo + vista + docker-compose con Postgres. *(no requiere n8n)*
- **Etapa 2 — Backend FastAPI:** capas + endpoints (ingest, sync, reels, labels, analysis) + tests. *(no requiere n8n corriendo; el sync se testea con ping/ingest mockeados)*
- **Etapa 3 — Ingesta n8n:** workflows ping + ingest + refresh token (validar wrinkle). *(requiere n8n instalado)*
- **Etapa 4 — Frontend:** tabla + etiquetado + "qué funciona" + detalle + sync UI.

Etapas 1 y 2 pueden avanzar mientras Luca instala n8n y hace el setup de Meta.

## 11. Límites honestos

- **Snapshot on-demand ≠ diario garantizado:** hay foto los días que abrís/actualizás; días sin abrir quedan sin snapshot. Sano para uso propio. Snapshots diarios garantizados → requieren always-on (VPS cron), v2.
- **Curva de retención segundo a segundo:** NO está en la API → para el análisis fino de un top se sigue mirando a mano en IG (por eso el detalle linkea al permalink).
- **Duración de video:** no disponible por insights → no hay "retención %"; se usa watch time promedio en segundos.
- **App Review de Meta:** al ser cuenta propia normalmente alcanza sin review; se confirma en el setup, no se asume.
- **Refresh de token en n8n:** depende de la API pública de n8n (wrinkle §8), se valida en Etapa 3.
