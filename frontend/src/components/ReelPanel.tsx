import { useEffect, useState } from "react";
import {
  DIMENSIONS, Dimension, LabelValue, ReelRow, ReelUpdate, SnapshotRow,
  patchReel, fetchReelHistory,
} from "../lib/api";
import { num, pct, sec, day } from "../lib/format";
import { buildClaudePrompt } from "../lib/claudePrompt";
import Sparkline from "./Sparkline";
import LabelCombobox from "./LabelCombobox";

interface Props {
  reel: ReelRow;
  labelOptions: Record<Dimension, LabelValue[]>;
  onSaved: (updated: ReelRow) => void;
  onClose: () => void;
}

const clean = (s: string): string | null => (s.trim() === "" ? null : s.trim());

const METRICS: { key: keyof ReelRow; label: string; fmt: (r: ReelRow) => string }[] = [
  { key: "reach", label: "Reach", fmt: (r) => num(r.reach) },
  { key: "views", label: "Views", fmt: (r) => num(r.views) },
  { key: "likes", label: "Likes", fmt: (r) => num(r.likes) },
  { key: "comments", label: "Comentarios", fmt: (r) => num(r.comments) },
  { key: "saved", label: "Guardados", fmt: (r) => num(r.saved) },
  { key: "shares", label: "Compartidos", fmt: (r) => num(r.shares) },
  { key: "engagement_rate", label: "Engagement", fmt: (r) => pct(r.engagement_rate) },
  { key: "save_rate", label: "Save rate", fmt: (r) => pct(r.save_rate) },
  { key: "share_rate", label: "Share rate", fmt: (r) => pct(r.share_rate) },
  { key: "avg_watch_time_sec", label: "Watch (s)", fmt: (r) => sec(r.avg_watch_time_sec) },
];

export default function ReelPanel({ reel, labelOptions, onSaved, onClose }: Props) {
  const [titulo, setTitulo] = useState(reel.titulo ?? "");
  const [guion, setGuion] = useState(reel.guion ?? "");
  const [dims, setDims] = useState<Record<Dimension, string>>({
    angulo: reel.angulo ?? "", formato: reel.formato ?? "", tipo_hook: reel.tipo_hook ?? "",
    categoria: reel.categoria ?? "", tema: reel.tema ?? "",
  });
  const [hist, setHist] = useState<SnapshotRow[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [copyMsg, setCopyMsg] = useState("");
  const [current, setCurrent] = useState<ReelRow>(reel);

  useEffect(() => { fetchReelHistory(reel.id).then(setHist).catch(() => {}); }, [reel.id]);

  async function save() {
    setSaving(true);
    const update: ReelUpdate = { titulo: clean(titulo), guion: clean(guion) };
    for (const { key } of DIMENSIONS) update[key] = clean(dims[key]);
    try {
      const updated = await patchReel(reel.id, update);
      setCurrent(updated);
      onSaved(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } finally {
      setSaving(false);
    }
  }

  async function copyPrompt() {
    // usa lo que está en el form (aunque no se haya guardado) para el prompt
    const merged: ReelRow = {
      ...current, titulo: clean(titulo), guion: clean(guion),
      angulo: clean(dims.angulo), formato: clean(dims.formato), tipo_hook: clean(dims.tipo_hook),
      categoria: clean(dims.categoria), tema: clean(dims.tema),
    };
    try {
      await navigator.clipboard.writeText(buildClaudePrompt(merged));
      setCopyMsg("Prompt copiado ✓");
    } catch {
      setCopyMsg("No se pudo copiar");
    }
    setTimeout(() => setCopyMsg(""), 3000);
  }

  const title = current.titulo || current.caption || current.ig_media_id;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Cerrar">✕</button>

        <div className="panel-grid">
          {/* Columna izquierda: media + métricas + historial */}
          <div className="panel-media">
            <div className="thumb-lg">
              {current.thumbnail_url
                ? <img src={current.thumbnail_url} alt="" />
                : <div className="thumb-ph"><span>▶</span></div>}
            </div>
            <div className="panel-meta-row">
              <span className="panel-date">{day(current.published_at)}</span>
              {current.permalink && (
                <a href={current.permalink} target="_blank" rel="noreferrer" className="link">Ver en Instagram ↗</a>
              )}
            </div>

            <div className="metrics-grid">
              {METRICS.map((m) => (
                <div className="metric" key={m.key}>
                  <span className="metric-label">{m.label}</span>
                  <span className="metric-value">{m.fmt(current)}</span>
                </div>
              ))}
            </div>

            <div className="charts">
              <div className="chart">
                <span className="chart-label">Reach en el tiempo</span>
                <Sparkline values={hist.map((h) => h.reach)} stroke="#1B2C6B" />
              </div>
              <div className="chart">
                <span className="chart-label">Engagement rate</span>
                <Sparkline values={hist.map((h) => h.engagement_rate)} stroke="#3D5BE0" />
              </div>
            </div>
          </div>

          {/* Columna derecha: edición + prompt */}
          <div className="panel-edit">
            <h2 className="panel-title">{title}</h2>

            <div className="field">
              <label>Título</label>
              <input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título corto del reel" />
            </div>

            <div className="dims">
              {DIMENSIONS.map(({ key, label }) => (
                <div className="field" key={key}>
                  <label>{label}</label>
                  <LabelCombobox
                    value={dims[key]}
                    options={labelOptions[key] ?? []}
                    onChange={(v) => setDims({ ...dims, [key]: v })}
                    placeholder="elegí o escribí uno nuevo"
                  />
                </div>
              ))}
            </div>

            <div className="field">
              <label>Guion</label>
              <textarea rows={6} value={guion} onChange={(e) => setGuion(e.target.value)}
                        placeholder="El guion completo del reel…" />
            </div>

            <div className="panel-actions">
              <button className="btn btn-primary" onClick={save} disabled={saving}>
                {saving ? "Guardando…" : saved ? "Guardado ✓" : "Guardar"}
              </button>
              <button className="btn btn-ghost" onClick={copyPrompt}>Copiar prompt para Claude</button>
              {copyMsg && <span className="sync-msg">{copyMsg}</span>}
            </div>
            <p className="hint">El prompt incluye todos los datos; los campos vacíos quedan como <code>[Formato]</code>, <code>[Guion]</code>, etc. para completar.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
