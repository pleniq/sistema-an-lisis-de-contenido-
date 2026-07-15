# Workflows de n8n — Laboratorio de Contenido

Dos workflows importables. **El ping queda 100% funcional al importarlo**; el de ingesta es el grafo real de nodos y necesita que le conectes tus credenciales de Meta (Etapa 0/3). No se pueden probar en vivo sin n8n corriendo + tu token de Instagram.

## Archivos

| Archivo | Rol |
|---|---|
| `ping-webhook.workflow.json` | Webhook `GET /webhook/lab-ping` que responde `200 {"status":"alive"}`. Es el **liveness**: el backend le pega antes de sincronizar para saber si n8n está prendido. |
| `ingest.workflow.json` | Webhook `POST /webhook/lab-ingest` (lo dispara el backend). Trae los Reels de la Graph API, arma el batch y lo postea a `POST /api/v1/ingest/instagram`. |
| `refresh-token.workflow.json` | Schedule cada ~50 días que renueva el long-lived token de Meta (ver wrinkle abajo). |

## Cómo importar

1. Abrí n8n → **Workflows** → menú **⋯** → **Import from File** → elegí el `.json`.
2. Importá los dos.
3. **Activá** cada workflow (toggle arriba a la derecha) para que el webhook quede vivo.

## Credenciales a crear (una vez)

### 1. `Meta IG Token (access_token)` — tipo **Query Auth**
Guarda el long-lived token de Instagram como query param (nunca queda en el JSON del workflow ni en la DB de la app).
- **Name:** `access_token`
- **Value:** tu long-lived token de Meta
- En los nodos **GET media** y **GET insights**, seleccioná esta credencial (aparecen con `id: "REEMPLAZAR"` hasta que la mapees).

### 2. Token de ingesta hacia el backend
El nodo **POST al backend** manda el header `X-Ingest-Token` leyendo `{{ $env.LAB_INGEST_TOKEN }}`.
- Arrancá n8n con esa variable de entorno, con el **mismo valor** que el `LAB_INGEST_TOKEN` del backend. Ej: `LAB_INGEST_TOKEN=... n8n start`.
- (Alternativa: reemplazar la expresión por una credencial Header Auth `X-Ingest-Token`.)

## Parámetros a editar (nodo "Parámetros" del workflow de ingesta)

```
igUserId         → el ID numérico de tu cuenta IG business
accountName      → nombre de la cuenta (ej. "Pleniq")
graphVersion     → v21.0 (o la vigente)
backendIngestUrl → http://localhost:8010/api/v1/ingest/instagram
```

> ⚠️ **Red n8n → backend:** si corrés n8n en **Docker**, `localhost` apunta al contenedor, no a tu Mac. Usá `http://host.docker.internal:8010/...`. Si corrés n8n con `npx n8n` (local), `localhost:8010` va bien.

## Conectar el backend con estos webhooks

En el `.env` del backend, completá con las URLs que te da n8n (Production URL de cada webhook):

```
LAB_N8N_PING_WEBHOOK_URL=http://localhost:5678/webhook/lab-ping
LAB_N8N_INGEST_WEBHOOK_URL=http://localhost:5678/webhook/lab-ingest
```

Con eso, `GET /api/v1/sync/status` va a devolver `n8n_alive: true` y el botón "Actualizar" del dashboard va a disparar la ingesta real.

## Notas de la Graph API (ver diseño)

- Métricas exactas (Reels): `reach, views, likes, comments, saved, shares, total_interactions, ig_reels_avg_watch_time, ig_reels_video_view_total_time`. `impressions` está deprecado; `plays` es ahora `views`.
- La paginación de `/media` se maneja en el nodo **GET media** (opción *pagination* → `paging.next`).
- Permisos necesarios en la app de Meta: `instagram_basic`, `instagram_manage_insights`, `pages_show_list` / `pages_read_engagement`.

## Refresh del token (`refresh-token.workflow.json`)

El long-lived token de Meta dura ~60 días. Este workflow corre por Schedule cada ~50 días (mientras n8n esté prendido) y lo renueva llamando a `GET /oauth/access_token?grant_type=fb_exchange_token`.

Variables de entorno que lee (en n8n): `META_APP_ID`, `META_APP_SECRET`, `IG_LONG_LIVED_TOKEN`.

> ⚠️ **Wrinkle (a validar en tu versión de n8n):** escribir el token renovado de vuelta en la **credencial** de n8n depende de la API pública (`PATCH /api/v1/credentials/{id}`), que no todas las versiones soportan para credenciales. El workflow deja el nuevo token en el output del nodo **Nuevo token**. Fallbacks:
> 1. Guardar el token en la variable de entorno `IG_LONG_LIVED_TOKEN` que leen los otros workflows (en vez de una credencial), y actualizar esa variable.
> 2. Copiar el nuevo token a mano a la credencial cuando el Schedule dispare (n8n puede notificarte).
>
> Como corre local y no siempre prendido, poné un recordatorio ~cada 50 días para abrir n8n y dejar que el Schedule corra, igual que con la ingesta.
