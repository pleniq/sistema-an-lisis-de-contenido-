import { useEffect, useState } from "react";
import { DIMENSIONS, Dimension, AnalysisRow, fetchAnalysis } from "../lib/api";
import { num, pct, sec } from "../lib/format";

export default function AnalisisPage() {
  const [groupBy, setGroupBy] = useState<Dimension>("formato");
  const [rows, setRows] = useState<AnalysisRow[]>([]);

  useEffect(() => { fetchAnalysis(groupBy).then(setRows).catch(() => setRows([])); }, [groupBy]);

  return (
    <>
      <div className="toolbar">
        <div className="toolbar-filters">
          <label className="select-label">Agrupar por</label>
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value as Dimension)}>
            {DIMENSIONS.map(({ key, label }) => <option key={key} value={key}>{label}</option>)}
          </select>
        </div>
        <span className="count">Promedios por grupo · ordenado por engagement</span>
      </div>

      <div className="card table-card">
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
                <td className="left"><span className="chip-tag">{r.grupo}</span></td>
                <td>{r.reels}</td>
                <td>{num(r.reach)}</td><td>{num(r.views)}</td><td>{num(r.likes)}</td>
                <td>{num(r.comments)}</td><td>{num(r.saved)}</td><td>{num(r.shares)}</td>
                <td className="strong">{pct(r.engagement_rate)}</td><td>{pct(r.save_rate)}</td>
                <td>{pct(r.share_rate)}</td><td>{sec(r.avg_watch_time_sec)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="empty-state">Todavía no hay datos etiquetados para agrupar.</p>}
      </div>
    </>
  );
}
