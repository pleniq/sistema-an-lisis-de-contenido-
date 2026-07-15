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
