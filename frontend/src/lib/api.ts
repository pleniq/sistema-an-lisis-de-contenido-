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

export interface LabelValue { id: string; name: string; count?: number; }

export interface LabelRenameResult { id: string; name: string; merged: boolean; }

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

export type TokenStatus = "ok" | "expired" | "missing";

export interface SyncStatus {
  running: boolean;
  last_synced_at: string | null;
  last_run: SyncRun | null;
  configured: boolean;
  token_status: TokenStatus;
  token_expires_at: string | null;
  days_left: number | null;
  account_name: string | null;
}

export interface RefreshResult {
  outcome: string;   // ok | skipped_fresh | not_configured | token_expired | already_running | error
  reels_processed?: number;
  snapshots_written?: number;
  detail?: string;
}

export interface MetaConfigStatus {
  connected: boolean;
  token_status: TokenStatus;
  ig_user_id: string | null;
  account_name: string | null;
  token_expires_at: string | null;
  days_left: number | null;
  long_lived: boolean;
  last_error: string | null;
}

export interface MetaConfigIn {
  access_token: string;
  ig_user_id?: string;
  account_name?: string;
  app_id?: string;
  app_secret?: string;
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

export const createLabel = (dim: Dimension, name: string): Promise<LabelValue> =>
  fetch(`/api/v1/labels/${dim}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  }).then(jsonOrThrow);

export const seedDefaultLabels = (): Promise<Record<string, number>> =>
  fetch("/api/v1/labels/seed-defaults", { method: "POST" }).then(jsonOrThrow);

export const renameLabel = (dim: Dimension, id: string, name: string): Promise<LabelRenameResult> =>
  fetch(`/api/v1/labels/${dim}/${id}`, {
    method: "PATCH", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  }).then(jsonOrThrow);

export const deleteLabel = (dim: Dimension, id: string): Promise<void> =>
  fetch(`/api/v1/labels/${dim}/${id}`, { method: "DELETE" }).then((r) => {
    if (!r.ok) throw new Error(`Error ${r.status}`);
  });

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

/** Dispara el sync (sincrónico). Devuelve el outcome del backend. */
export const triggerRefresh = (force: boolean): Promise<RefreshResult> =>
  fetch(`/api/v1/sync/refresh?force=${force}&trigger=manual`, { method: "POST" })
    .then(async (r) => (r.status === 409 ? { outcome: "already_running" } : r.json()));

export const fetchMetaConfig = (): Promise<MetaConfigStatus> =>
  fetch("/api/v1/config/meta").then(jsonOrThrow);

export const saveMetaConfig = (data: MetaConfigIn): Promise<MetaConfigStatus> =>
  fetch("/api/v1/config/meta", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then(jsonOrThrow);
