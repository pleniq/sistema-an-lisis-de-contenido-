import { useMemo, useState } from "react";
import { DIMENSIONS, Dimension, ReelRow, exportReels } from "../lib/api";
import { num, pct, sec, day } from "../lib/format";
import { useApp } from "../lib/appContext";
import ReelLabelEditor from "../components/ReelLabelEditor";
import ReelDetail from "../components/ReelDetail";

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
  const [detail, setDetail] = useState<ReelRow | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [copyMsg, setCopyMsg] = useState("");

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
      if (av == null) return 1;
      if (bv == null) return -1;
      return (av as any) < (bv as any) ? -dir : (av as any) > (bv as any) ? dir : 0;
    });
  }, [reels, filters, sortKey, sortDir]);

  const arrow = (key: SortKey) => (key === sortKey ? (sortDir === "asc" ? " ▲" : " ▼") : "");

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const allVisibleSelected = rows.length > 0 && rows.every((r) => selected.has(r.id));
  function toggleAll() {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allVisibleSelected) rows.forEach((r) => next.delete(r.id));
      else rows.forEach((r) => next.add(r.id));
      return next;
    });
  }

  async function copyForClaude() {
    if (selected.size === 0) return;
    setCopyMsg("Copiando…");
    try {
      const res = await exportReels([...selected]);
      await navigator.clipboard.writeText(res.text);
      setCopyMsg(`Copiado: ${res.reels} reels al portapapeles`);
    } catch {
      setCopyMsg("No se pudo copiar (permiso de portapapeles)");
    }
    setTimeout(() => setCopyMsg(""), 4000);
  }

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
        <button className="btn" onClick={copyForClaude} disabled={selected.size === 0}>
          Copiar para Claude ({selected.size})
        </button>
        {copyMsg && <span className="sync-msg">{copyMsg}</span>}
        <span className="count">{rows.length} reels</span>
      </div>

      <table>
        <thead>
          <tr>
            <th><input type="checkbox" checked={allVisibleSelected} onChange={toggleAll} /></th>
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
            <tr key={r.id} className={selected.has(r.id) ? "sel" : ""}>
              <td><input type="checkbox" checked={selected.has(r.id)} onChange={() => toggleOne(r.id)} /></td>
              <td className="left">
                <button className="link" onClick={() => setDetail(r)}>{r.titulo || r.caption || r.ig_media_id}</button>
              </td>
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
      {detail && <ReelDetail reel={detail} onClose={() => setDetail(null)} />}
    </>
  );
}
