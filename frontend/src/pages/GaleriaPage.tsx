import { useMemo, useState } from "react";
import { DIMENSIONS, Dimension, ReelRow, exportReels } from "../lib/api";
import { num, pct, day } from "../lib/format";
import { useApp } from "../lib/appContext";
import ReelPanel from "../components/ReelPanel";

export default function GaleriaPage() {
  const { reels, labelOptions, updateReel, reloadLabels } = useApp();
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [filters, setFilters] = useState<Record<Dimension, string>>({
    angulo: "", formato: "", tipo_hook: "", categoria: "", tema: "",
  });
  const [open, setOpen] = useState<ReelRow | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [copyMsg, setCopyMsg] = useState("");

  const rows = useMemo(() => {
    const filtered = reels.filter((r) =>
      DIMENSIONS.every(({ key }) => !filters[key] || r[key] === filters[key]));
    const dir = order === "asc" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = a.published_at, bv = b.published_at;
      if (!av && !bv) return 0;
      if (!av) return 1;
      if (!bv) return -1;
      return av < bv ? -dir : av > bv ? dir : 0;
    });
  }, [reels, filters, order]);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function copyForClaude() {
    if (selected.size === 0) return;
    setCopyMsg("Copiando…");
    try {
      const res = await exportReels([...selected]);
      await navigator.clipboard.writeText(res.text);
      setCopyMsg(`Copiado · ${res.reels} reels`);
    } catch {
      setCopyMsg("No se pudo copiar");
    }
    setTimeout(() => setCopyMsg(""), 3500);
  }

  return (
    <>
      <div className="toolbar">
        <div className="toolbar-filters">
          <button className="pill-toggle" onClick={() => setOrder(order === "desc" ? "asc" : "desc")}>
            Fecha {order === "desc" ? "↓ más nuevos" : "↑ más viejos"}
          </button>
          {DIMENSIONS.map(({ key, label }) => (
            <select key={key} value={filters[key]}
                    onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}>
              <option value="">{label}: todos</option>
              {(labelOptions[key] ?? []).map((o) => <option key={o.id} value={o.name}>{o.name}</option>)}
            </select>
          ))}
        </div>
        <div className="toolbar-right">
          {copyMsg && <span className="sync-msg">{copyMsg}</span>}
          <button className="btn btn-ghost" onClick={copyForClaude} disabled={selected.size === 0}>
            Copiar para Claude ({selected.size})
          </button>
          <span className="count">{rows.length} reels</span>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="empty-state">
          <p>Todavía no hay reels.</p>
          <p className="hint">Andá a <b>Configuración</b>, pegá tu token de Meta y actualizá.</p>
        </div>
      ) : (
        <div className="gallery">
          {rows.map((r) => {
            const chips = [r.angulo, r.formato, r.categoria].filter(Boolean) as string[];
            return (
              <article key={r.id} className={`reel-card ${selected.has(r.id) ? "sel" : ""}`}
                       onClick={() => setOpen(r)}>
                <div className="reel-thumb">
                  {r.thumbnail_url
                    ? <img src={r.thumbnail_url} alt="" loading="lazy" />
                    : <div className="thumb-ph"><span>▶</span></div>}
                  <label className="reel-check" onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={selected.has(r.id)} onChange={() => toggle(r.id)} />
                  </label>
                  <span className="reel-date">{day(r.published_at)}</span>
                </div>
                <div className="reel-body">
                  <p className="reel-title">{r.titulo || r.caption || r.ig_media_id}</p>
                  <div className="reel-stats">
                    <span><b>{num(r.reach)}</b> reach</span>
                    <span><b>{pct(r.engagement_rate)}</b> ER</span>
                  </div>
                  <div className="reel-chips">
                    {chips.length
                      ? chips.map((t, i) => <span key={i} className="chip-tag">{t}</span>)
                      : <span className="chip-tag chip-empty">sin etiquetar</span>}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {open && (
        <ReelPanel
          reel={open}
          labelOptions={labelOptions}
          reloadLabels={reloadLabels}
          onSaved={(u) => { updateReel(u); reloadLabels(); setOpen(u); }}
          onClose={() => setOpen(null)}
        />
      )}
    </>
  );
}
