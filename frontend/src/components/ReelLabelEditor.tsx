import { useState } from "react";
import { DIMENSIONS, Dimension, LabelValue, ReelRow, ReelUpdate, patchReel } from "../lib/api";

interface Props {
  reel: ReelRow;
  labelOptions: Record<Dimension, LabelValue[]>;
  onSaved: (updated: ReelRow) => void;
  onClose: () => void;
}

const clean = (s: string): string | null => (s.trim() === "" ? null : s.trim());

export default function ReelLabelEditor({ reel, labelOptions, onSaved, onClose }: Props) {
  const [titulo, setTitulo] = useState(reel.titulo ?? "");
  const [guion, setGuion] = useState(reel.guion ?? "");
  const [dims, setDims] = useState<Record<Dimension, string>>({
    angulo: reel.angulo ?? "", formato: reel.formato ?? "", tipo_hook: reel.tipo_hook ?? "",
    categoria: reel.categoria ?? "", tema: reel.tema ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    const update: ReelUpdate = { titulo: clean(titulo), guion: clean(guion) };
    for (const { key } of DIMENSIONS) update[key] = clean(dims[key]);
    try {
      const updated = await patchReel(reel.id, update);
      onSaved(updated);
    } catch (e) {
      setError((e as Error).message);
      setSaving(false);
    }
  }

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <strong>Etiquetar reel</strong>
          <button className="link" onClick={onClose}>cerrar</button>
        </div>
        <div className="field">
          <label>Título</label>
          <input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título corto" />
        </div>
        <div className="field">
          <label>Guion</label>
          <textarea rows={6} value={guion} onChange={(e) => setGuion(e.target.value)}
                    placeholder="El guion completo del reel…" />
        </div>
        {DIMENSIONS.map(({ key, label }) => (
          <div className="field" key={key}>
            <label>{label}</label>
            <input
              list={`dl-${key}`}
              value={dims[key]}
              onChange={(e) => setDims({ ...dims, [key]: e.target.value })}
              placeholder="elegí o escribí uno nuevo"
            />
            <datalist id={`dl-${key}`}>
              {(labelOptions[key] ?? []).map((o) => <option key={o.id} value={o.name} />)}
            </datalist>
          </div>
        ))}
        {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
        <div className="drawer-actions">
          <button className="btn" onClick={save} disabled={saving}>{saving ? "Guardando…" : "Guardar"}</button>
          <button className="link" onClick={onClose}>Cancelar</button>
        </div>
      </aside>
    </div>
  );
}
