export type Dimension = "angulo" | "formato" | "tipo_hook" | "categoria" | "tema";

export const DIMENSIONS: { key: Dimension; label: string }[] = [
  { key: "angulo", label: "Ángulo" },
  { key: "formato", label: "Formato" },
  { key: "tipo_hook", label: "Tipo de hook" },
  { key: "categoria", label: "Categoría" },
  { key: "tema", label: "Tema" },
];

export interface ReelRow {
  id: string; ig_media_id: string; titulo: string | null; caption: string | null;
  guion: string | null; permalink: string | null; thumbnail_url: string | null;
  published_at: string | null;
  angulo: string | null; formato: string | null; tipo_hook: string | null;
  categoria: string | null; tema: string | null;
  reach: number | null; views: number | null; likes: number | null;
  comments: number | null; saved: number | null; shares: number | null;
  total_interactions: number | null; avg_watch_time_sec: number | null;
  engagement_rate: number | null; save_rate: number | null; share_rate: number | null;
}

export interface ReelUpdate {
  titulo?: string | null; guion?: string | null;
  angulo?: string | null; formato?: string | null; tipo_hook?: string | null;
  categoria?: string | null; tema?: string | null;
}

export interface LabelValue { id: string; name: string; }

export interface AnalysisRow {
  grupo: string; reels: number;
  reach: number | null; views: number | null; likes: number | null;
  comments: number | null; saved: number | null; shares: number | null;
  total_interactions: number | null; avg_watch_time_sec: number | null;
  engagement_rate: number | null; save_rate: number | null; share_rate: number | null;
}

export interface SnapshotRow {
  snapshot_date: string;
  reach: number | null; views: number | null; likes: number | null;
  comments: number | null; saved: number | null; shares: number | null;
  total_interactions: number | null; avg_watch_time_sec: number | null;
  engagement_rate: number | null; save_rate: number | null; share_rate: number | null;
}

export interface ExportResponse { format: string; reels: number; text: string; }

export interface SyncRun {
  id: string; trigger: string; status: string;
  started_at: string | null; finished_at: string | null;
  reels_processed: number; snapshots_written: number; error_detail: string | null;
}

export interface SyncStatus {
  n8n_alive: boolean; running: boolean;
  last_synced_at: string | null; last_run: SyncRun | null;
}

async function jsonOrThrow(res: Response) {
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

export const fetchReels = (): Promise<ReelRow[]> =>
  fetch("/api/v1/reels").then(jsonOrThrow);

export const patchReel = (id: string, update: ReelUpdate): Promise<ReelRow> =>
  fetch(`/api/v1/reels/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  }).then(jsonOrThrow);

export const fetchLabels = (dim: Dimension): Promise<LabelValue[]> =>
  fetch(`/api/v1/labels/${dim}`).then(jsonOrThrow);

export const fetchAnalysis = (groupBy: Dimension): Promise<AnalysisRow[]> =>
  fetch(`/api/v1/analysis?group_by=${groupBy}`).then(jsonOrThrow);

export const fetchReelHistory = (id: string): Promise<SnapshotRow[]> =>
  fetch(`/api/v1/reels/${id}/history`).then(jsonOrThrow);

export const exportReels = (ids: string[]): Promise<ExportResponse> =>
  fetch("/api/v1/reels/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reel_ids: ids }),
  }).then(jsonOrThrow);

export const fetchSyncStatus = (): Promise<SyncStatus> =>
  fetch("/api/v1/sync/status").then(jsonOrThrow);

/** Dispara el sync. Devuelve el código HTTP (202 started, 409 running, 503 n8n down, 200 fresh). */
export const triggerRefresh = (force: boolean): Promise<number> =>
  fetch(`/api/v1/sync/refresh?force=${force}&trigger=manual`, { method: "POST" }).then((r) => r.status);
