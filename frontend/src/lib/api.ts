export interface ReelRow {
  id: string; ig_media_id: string; titulo: string | null; caption: string | null;
  permalink: string | null; published_at: string | null;
  reach: number | null; views: number | null; likes: number | null;
  comments: number | null; saved: number | null; shares: number | null;
  total_interactions: number | null; avg_watch_time_sec: number | null;
  engagement_rate: number | null; save_rate: number | null; share_rate: number | null;
}

export interface SyncRun {
  id: string; trigger: string; status: string;
  started_at: string | null; finished_at: string | null;
  reels_processed: number; snapshots_written: number; error_detail: string | null;
}

export interface SyncStatus {
  n8n_alive: boolean; running: boolean;
  last_synced_at: string | null; last_run: SyncRun | null;
}

export async function fetchReels(): Promise<ReelRow[]> {
  const res = await fetch("/api/v1/reels");
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

export async function fetchSyncStatus(): Promise<SyncStatus> {
  const res = await fetch("/api/v1/sync/status");
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}

/** Dispara el sync. Devuelve el código HTTP (202 started, 409 running, 503 n8n down, 200 fresh). */
export async function triggerRefresh(force: boolean): Promise<number> {
  const res = await fetch(`/api/v1/sync/refresh?force=${force}&trigger=manual`, { method: "POST" });
  return res.status;
}
