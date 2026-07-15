import { useEffect, useState } from "react";
import { ReelRow, SnapshotRow, fetchReelHistory } from "../lib/api";
import { num, pct, sec, day } from "../lib/format";
import Sparkline from "./Sparkline";

interface Props {
  reel: ReelRow;
  onClose: () => void;
}

export default function ReelDetail({ reel, onClose }: Props) {
  const [hist, setHist] = useState<SnapshotRow[]>([]);

  useEffect(() => { fetchReelHistory(reel.id).then(setHist).catch(() => {}); }, [reel.id]);

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <strong>{reel.titulo || reel.caption || reel.ig_media_id}</strong>
          <button className="link" onClick={onClose}>cerrar</button>
        </div>

        {reel.thumbnail_url && <img className="thumb" src={reel.thumbnail_url} alt="" />}

        <div className="detail-meta">
          <span>Publicado: {day(reel.published_at)}</span>
          {reel.permalink && <a href={reel.permalink} target="_blank" rel="noreferrer">ver en Instagram ↗</a>}
        </div>

        <div className="detail-tags">
          {[reel.angulo, reel.formato, reel.tipo_hook, reel.categoria, reel.tema]
            .filter(Boolean).map((t, i) => <span key={i} className="pill">{t}</span>)}
        </div>

        <div className="detail-metrics">
          <div><span className="k">Reach</span><span className="v">{num(reel.reach)}</span></div>
          <div><span className="k">Views</span><span className="v">{num(reel.views)}</span></div>
          <div><span className="k">ER</span><span className="v">{pct(reel.engagement_rate)}</span></div>
          <div><span className="k">Save%</span><span className="v">{pct(reel.save_rate)}</span></div>
          <div><span className="k">Share%</span><span className="v">{pct(reel.share_rate)}</span></div>
          <div><span className="k">Watch (s)</span><span className="v">{sec(reel.avg_watch_time_sec)}</span></div>
        </div>

        <h4 className="detail-h">Historial ({hist.length} snapshot{hist.length === 1 ? "" : "s"})</h4>
        <div className="charts">
          <div className="chart">
            <span className="chart-label">Reach</span>
            <Sparkline values={hist.map((h) => h.reach)} stroke="#2563eb" />
          </div>
          <div className="chart">
            <span className="chart-label">Engagement rate</span>
            <Sparkline values={hist.map((h) => h.engagement_rate)} stroke="#16a34a" />
          </div>
        </div>

        {reel.guion && (
          <>
            <h4 className="detail-h">Guion</h4>
            <p className="guion">{reel.guion}</p>
          </>
        )}
      </aside>
    </div>
  );
}
