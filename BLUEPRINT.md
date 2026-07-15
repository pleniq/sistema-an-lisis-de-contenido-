# Laboratorio de Contenido — Blueprint del servicio

> Documento maestro. Cuenta el problema, la solución y todo lo que vamos a construir.
> Detalle técnico completo: [`docs/superpowers/specs/2026-07-15-laboratorio-contenido-design.md`](docs/superpowers/specs/2026-07-15-laboratorio-contenido-design.md)
>
> **Estado:** diseño aprobado, sin código todavía. Fecha: 2026-07-15.

---

## 1. Qué es

Un dashboard interno ("laboratorio de contenido") que jala **solo las métricas** de cada Reel de Instagram desde la API oficial (nada de screenshots), me deja **etiquetar** cada Reel por ángulo / formato / hook / categoría / tema, y me muestra **objetivamente qué tipo de contenido promedia mejores números**. Además, **exporta** toda esa data lista para pegar en Claude Code y planificar el contenido de la semana siguiente.

Uso interno mío hoy. Activo reutilizable como servicio para clientes a futuro (por eso el modelo tiene `account_id` desde el día 1).

---

## 2. El problema que estoy teniendo

**Problema principal (el que me duele hoy):** hago contenido orgánico (Reels) y la parte que más tiempo y aburrimiento me lleva es sacar screenshots de las métricas de cada video, uno por uno, para compararlos. Con esa comparación detecto ángulos ganadores, formatos que funcionan y tipo de contenido que más llama la atención. Los guiones no quiero automatizarlos (ahí está mi criterio y voz), pero **jalar y comparar métricas sí**, y eso es puro trabajo manual y tedioso.

**Problema secundario (de contexto, apareció al diseñar):** todo esto corre **local**, no en un servidor prendido 24/7. Un cron diario (ej. "actualizar a las 6am") de n8n **solo dispara si n8n está corriendo en ese momento**. Como la máquina está apagada la mayor parte del tiempo, ese disparo se perdería en silencio — y con él, el snapshot del día, que es **lo único que no se puede recuperar**. Un schedule en una instancia local es el mecanismo de disparo equivocado.

---

## 3. Cómo lo vamos a solucionar

**Contra el problema principal:** un sistema que automatiza la ingesta y la comparación de métricas.
- n8n pega a la Graph API oficial y trae las métricas de cada Reel.
- Postgres las guarda con una **foto diaria (snapshot)** por reel — el historial que no se recupera después.
- El dashboard muestra una tabla densa ordenable, permite etiquetar cada reel en ~10 seg (una sola vez), y tiene la vista **"qué funciona"**: agrupa por ángulo/formato/categoría y muestra el promedio de cada métrica por grupo. Ese es el corazón del sistema.
- Ranking honesto, sin "score mágico": ordena por la métrica que yo elija + 3 ratios sobre alcance → engagement rate, tasa de guardados, tasa de compartidos.

**Contra el problema de contexto (local, no siempre prendido):** el disparo pasa a ser **on-demand** — se actualiza cuando yo uso el sistema, no por reloj. Con 3 guardas para que no se rompa:
1. **Frescura ("entrar sin actualizar"):** si sincronicé hace menos de 5 min, entro con lo que hay (salí y volví, no cambió nada).
2. **Lock + indicador:** si ya hay una actualización corriendo y aprieto de nuevo, no dispara otra; la UI muestra "actualizando…". Si una corrida queda colgada >10 min (cerré la máquina a mitad), se considera muerta y se permite una nueva.
3. **Liveness de n8n:** antes de actualizar, el backend le pega a un webhook de "ping" de n8n; si devuelve 200, n8n está vivo y dispara la actualización real; si no, la UI avisa "n8n apagado".
- Se actualiza **automáticamente al abrir** (si está viejo) **y** con un **botón manual** — las dos, como quería.

**El puente con Claude Code:** botón "Copiar para Claude". Selecciono 1 o varios reels y copio al portapapeles un texto compacto (markdown, mínimo de tokens sin perder precisión) con título + guion + formato + etiquetas + todas las stats. Así, cuando le digo a Claude "analizá el contenido que subí y armá la semana que viene", ya tiene toda la data de qué dije, qué formato, y cómo viene rindiendo cada pieza.

---

## 4. Cómo funciona (flujo end-to-end)

```
Abro el sistema (o aprieto "Actualizar")
   │
   ▼
Backend  ── ¿ya corriendo? (lock) · ¿n8n vivo? (ping) · ¿datos viejos? (frescura)
   │  si todo OK, dispara →
   ▼
 n8n  ── GET media (solo Reels) + insights por reel (token, paginación, retries)
   │  POST batch →
   ▼
Backend  /api/v1/ingest/instagram  ── upsert por ig_media_id + snapshot del día (idempotente)
   │
   ▼
PostgreSQL  ── una foto por reel por día + mis etiquetas y guiones
   │
   ▼
Front  ── tabla ordenable · etiquetado · vista "qué funciona" · detalle · "Copiar para Claude"
```

---

## 5. Qué construimos (componentes)

| Componente | Rol |
|---|---|
| **PostgreSQL + Alembic** | Datos: cuentas, reels (+ mis etiquetas y guiones), snapshots diarios, log de corridas, vista de últimas métricas + ratios. |
| **Backend FastAPI** (3 capas) | Orquesta el sync (lock/liveness/frescura), recibe la ingesta, sirve la tabla/análisis/detalle, edita etiquetas y guiones, arma el export para Claude. Toda la lógica de negocio testeable en Python. |
| **n8n** (2-3 workflows) | Pega a la Graph API y postea al backend. Webhook de ping (liveness), webhook de ingesta, y refresh del token (~60 días). Reutilizable para clientes. |
| **Front React + Vite** | Dashboard: tabla densa, etiquetado rápido, vista "qué funciona", detalle con historial, sync UI (botón + indicador), selección múltiple + "Copiar para Claude". |

**Decisiones clave ya tomadas:** lógica de ingesta en el backend (n8n fino) · token en la credencial de n8n (nunca en la DB de la app) · sin login en v1 (corre local; el endpoint de ingesta igual lleva un token máquina-a-máquina) · disparo on-demand · una tabla por dimensión de etiqueta (SQL-first, agrupación limpia).

---

## 6. Métricas verificadas (Graph API oficial, verificado 2026-07-15)

Nombres EXACTOS de campos para Reels en `GET /{ig-media-id}/insights`:

`reach` · `views` (⚠️ el viejo `plays` ahora es `views`) · `likes` · `comments` · `saved` · `shares` · `total_interactions` · `ig_reels_avg_watch_time` (en **ms**) · `ig_reels_video_view_total_time` (en **ms**).

Límites honestos confirmados:
- `impressions` está deprecado (contenido post 2-jul-2024) → usamos `reach`.
- La **duración del video no viene** por la API → nada de "retención %"; solo watch time promedio en segundos.
- La **curva de retención segundo a segundo no está** en la API → para el análisis fino de un top, se sigue mirando a mano en IG (por eso el detalle linkea al permalink).

---

## 7. Plan por etapas y estado

| Etapa | Qué | Estado | Necesita n8n |
|---|---|---|---|
| 0 | Setup Meta/IG + **instalar n8n local** (IG↔Página FB, app en Meta, long-lived token, credencial n8n) | Luca lo está haciendo | — |
| 1 | DB + Alembic (schema + vista + docker-compose Postgres) | Pendiente | No |
| 2 | Backend FastAPI (capas + endpoints + tests) | Pendiente | No (mocks) |
| 3 | Ingesta n8n (ping + ingest + refresh token) | Pendiente | Sí |
| 4 | Frontend (tabla + etiquetado + "qué funciona" + detalle + export) | Pendiente | — |

Las etapas 1 y 2 pueden avanzar mientras se instala n8n y se hace el setup de Meta. **No se toca código hasta el OK del plan de implementación.**

---

## 8. Fuera de alcance ahora (v2)

Etiquetado asistido por IA (sugerir formato/categoría leyendo el caption) · selector multi-cuenta · vista "primeras 48h" (comparar reels a igualdad de tiempo) · deploy always-on en VPS con snapshots diarios garantizados por cron.

---

## 9. Un límite honesto de v1

Con disparo on-demand, hay **snapshot los días que abro/actualizo el sistema**, no garantizado todos los días. Para mi uso es sano (lo abro seguido). Snapshots diarios garantizados aunque no lo mire → requieren algo siempre prendido (VPS), y eso es v2, cuando pase a servicio para clientes.
