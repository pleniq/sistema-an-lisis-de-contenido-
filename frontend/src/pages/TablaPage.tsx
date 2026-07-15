import { useMemo, useState } from "react";
import { DIMENSIONS, Dimension, ReelRow } from "../lib/api";
import { num, pct, sec, day } from "../lib/format";
import { useApp } from "../lib/appContext";
import ReelLabelEditor from "../components/ReelLabelEditor";

type SortKey = keyof ReelRow;
const COLS: { key: SortKey; label: string; fmt: (r: ReelRow) => string }[] = [
  { key: "reach", label: "Reach", fmt: (r) => num(r.reach) },
  { key: "views", label: "Views", fmt: (r) => num(r.views) },
  { key: "likes", label: "Likes", fmt: (r) => num(r.likes) },
  { key: "comments", label: "Coment.", fmt: (r) => num(r.comments) },
  { key: "saved", label: "Saves", fmt: (r) => num(r.saved) },
  { key: "shares", label: "Shares", fmt: (r) => num(r.shares) },
  { key: "engagement_rate", label: "ER", fmt: (r) => pct(r.engagement_rate) },
  { key: "save_rate", label: "Save%", fmt: (r) => pct(r.save_rate) },
  { key: "share_rate", label: "Share%", fmt: (r) => pct(r.share_rate) },
  { key: "avg_watch_time_sec", label: "Watch (s)", fmt: (r) => sec(r.avg_watch_time_sec) },
];

export default function TablaPage() {
  const { reels, labelOptions, updateReel, reloadLabels } = useApp();
  const [sortKey, setSortKey] = useState<SortKey>("published_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [filters, setFilters] = useState<Record<Dimension, string>>({
    angulo: "", formato: "", tipo_hook: "", categoria: "", tema: "",
  });
  const [editing, setEditing] = useState<ReelRow | null>(null);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("desc"); }
  }

  const rows = useMemo(() => {
    const filtered = reels.filter((r) =>
      DIMENSIONS.every(({ key }) => !filters[key] || r[key] === filters[key]));
    const dir = sortDir === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = a[sortKey] as number | string | null;
      const bv = b[sortKey] as number | string | null;
      if (av == null && bv == null) return 0;
      if (av == null) return 1;      // nulls al final
      if (bv == null) return -1;
      return (av as any) < (bv as any) ? -dir : (av as any) > (bv as any) ? dir : 0;
    });
  }, [reels, filters, sortKey, sortDir]);

  const arrow = (key: SortKey) => (key === sortKey ? (sortDir === "asc" ? " ▲" : " ▼") : "");

  return (
    <>
      <div className="filters">
        {DIMENSIONS.map(({ key, label }) => (
          <label key={key} className="filter">
            {label}:
            <select value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}>
              <option value="">todos</option>
              {(labelOptions[key] ?? []).map((o) => <option key={o.id} value={o.name}>{o.name}</option>)}
            </select>
          </label>
        ))}
        <span className="count">{rows.length} reels</span>
      </div>

      <table>
        <thead>
          <tr>
            <th className="sortable" onClick={() => toggleSort("titulo")}>Título / Caption{arrow("titulo")}</th>
            <th className="sortable" onClick={() => toggleSort("published_at")}>Publicado{arrow("published_at")}</th>
            <th>Ángulo</th><th>Formato</th><th>Categoría</th>
            {COLS.map((c) => (
              <th key={c.key} className="sortable" onClick={() => toggleSort(c.key)}>{c.label}{arrow(c.key)}</th>
            ))}
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td className="left">{r.titulo || r.caption || r.ig_media_id}</td>
              <td>{day(r.published_at)}</td>
              <td className="left tag">{r.angulo || "—"}</td>
              <td className="left tag">{r.formato || "—"}</td>
              <td className="left tag">{r.categoria || "—"}</td>
              {COLS.map((c) => <td key={c.key}>{c.fmt(r)}</td>)}
              <td><button className="link" onClick={() => setEditing(r)}>etiquetar</button></td>
            </tr>
          ))}
        </tbody>
      </table>

      {editing && (
        <ReelLabelEditor
          reel={editing}
          labelOptions={labelOptions}
          onSaved={(updated) => { updateReel(updated); reloadLabels(); setEditing(null); }}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
