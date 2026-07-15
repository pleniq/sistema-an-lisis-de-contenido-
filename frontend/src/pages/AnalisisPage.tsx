import { useEffect, useState } from "react";
import { DIMENSIONS, Dimension, AnalysisRow, fetchAnalysis } from "../lib/api";
import { num, pct, sec } from "../lib/format";

export default function AnalisisPage() {
  const [groupBy, setGroupBy] = useState<Dimension>("formato");
  const [rows, setRows] = useState<AnalysisRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalysis(groupBy).then(setRows).catch((e) => setError(e.message));
  }, [groupBy]);

  return (
    <>
      <div className="filters">
        <label className="filter">
          Agrupar por:
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value as Dimension)}>
            {DIMENSIONS.map(({ key, label }) => <option key={key} value={key}>{label}</option>)}
          </select>
        </label>
        <span className="count">Promedios por grupo · ordenado por ER</span>
      </div>
      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
      <table>
        <thead>
          <tr>
            <th>Grupo</th><th>Reels</th><th>Reach</th><th>Views</th><th>Likes</th>
            <th>Coment.</th><th>Saves</th><th>Shares</th>
            <th>ER</th><th>Save%</th><th>Share%</th><th>Watch (s)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.grupo}>
              <td className="left tag">{r.grupo}</td>
              <td>{r.reels}</td>
              <td>{num(r.reach)}</td><td>{num(r.views)}</td><td>{num(r.likes)}</td>
              <td>{num(r.comments)}</td><td>{num(r.saved)}</td><td>{num(r.shares)}</td>
              <td>{pct(r.engagement_rate)}</td><td>{pct(r.save_rate)}</td>
              <td>{pct(r.share_rate)}</td><td>{sec(r.avg_watch_time_sec)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length === 0 && !error && <p className="empty">Todavía no hay datos etiquetados para agrupar.</p>}
    </>
  );
}
