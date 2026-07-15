import { useCallback, useEffect, useState } from "react";
import { fetchReels, ReelRow } from "./lib/api";
import { useSync } from "./lib/useSync";
import SyncBar from "./components/SyncBar";

const pct = (v: number | null) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const num = (v: number | null) => (v == null ? "—" : v.toLocaleString("es-AR"));

export default function App() {
  const [reels, setReels] = useState<ReelRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadReels = useCallback(() => {
    fetchReels().then(setReels).catch((e) => setError(e.message));
  }, []);

  const { status, syncing, message, refresh } = useSync(loadReels);

  useEffect(() => { loadReels(); }, [loadReels]);

  return (
    <div className="wrap">
      <header className="topbar">
        <h1>Laboratorio de Contenido</h1>
        <SyncBar status={status} syncing={syncing} message={message} onRefresh={() => refresh(true)} />
      </header>
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
