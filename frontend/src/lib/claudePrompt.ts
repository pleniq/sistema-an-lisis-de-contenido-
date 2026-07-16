import { ReelRow } from "./api";
import { num, pct, sec, day } from "./format";

/** Devuelve el valor si está cargado, o `[Placeholder]` si está vacío. */
function slot(value: string | null | undefined, placeholder: string): string {
  return value && value.trim() ? value.trim() : `[${placeholder}]`;
}

/**
 * Arma el prompt para pegar en Claude Code con TODOS los datos del reel.
 * Los campos manuales vacíos quedan como placeholders `[Campo]` para completar.
 */
export function buildClaudePrompt(r: ReelRow): string {
  const lines: string[] = [
    "Analizá este reel de Instagram y ayudame a planificar contenido.",
    "",
    `Título: ${slot(r.titulo, "Título")}`,
    `Publicado: ${r.published_at ? day(r.published_at) : "[Fecha]"}`,
    `Ángulo: ${slot(r.angulo, "Ángulo")}`,
    `Formato: ${slot(r.formato, "Formato")}`,
    `Tipo de hook: ${slot(r.tipo_hook, "Tipo de hook")}`,
    `Categoría: ${slot(r.categoria, "Categoría")}`,
    `Tema: ${slot(r.tema, "Tema")}`,
    "",
    "Guion:",
    slot(r.guion, "Guion"),
    "",
    "Métricas:",
    `- Reach: ${num(r.reach)}`,
    `- Views: ${num(r.views)}`,
    `- Likes: ${num(r.likes)}`,
    `- Comentarios: ${num(r.comments)}`,
    `- Guardados: ${num(r.saved)}`,
    `- Compartidos: ${num(r.shares)}`,
    `- Interacciones totales: ${num(r.total_interactions)}`,
    `- Engagement rate: ${pct(r.engagement_rate)}`,
    `- Save rate: ${pct(r.save_rate)}`,
    `- Share rate: ${pct(r.share_rate)}`,
    `- Watch time promedio: ${sec(r.avg_watch_time_sec)} s`,
  ];
  if (r.permalink) lines.push("", `Permalink: ${r.permalink}`);
  return lines.join("\n");
}
