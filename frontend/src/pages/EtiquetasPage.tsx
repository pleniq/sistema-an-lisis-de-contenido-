import { useEffect, useState } from "react";
import {
  DIMENSIONS, Dimension, LabelValue,
  fetchLabels, createLabel, renameLabel, deleteLabel, seedDefaultLabels,
} from "../lib/api";

function LabelRow({ v, onRename, onDelete }: {
  v: LabelValue; onRename: (name: string) => void; onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(v.name);
  useEffect(() => setName(v.name), [v.name]);

  function commit() {
    setEditing(false);
    const clean = name.trim();
    if (clean && clean !== v.name) onRename(clean);
    else setName(v.name);
  }

  return (
    <li className="label-row">
      {editing ? (
        <input className="label-edit" autoFocus value={name}
               onChange={(e) => setName(e.target.value)}
               onBlur={commit}
               onKeyDown={(e) => {
                 if (e.key === "Enter") commit();
                 if (e.key === "Escape") { setName(v.name); setEditing(false); }
               }} />
      ) : (
        <span className="label-name" onClick={() => setEditing(true)} title="Click para renombrar">{v.name}</span>
      )}
      <span className="label-count" title="Reels que la usan">{v.count ?? 0}</span>
      <button className="label-del" onClick={onDelete} title="Borrar">✕</button>
    </li>
  );
}

function DimensionManager({ dim, label }: { dim: Dimension; label: string }) {
  const [values, setValues] = useState<LabelValue[]>([]);
  const [newName, setNewName] = useState("");
  const [msg, setMsg] = useState("");

  function load() { fetchLabels(dim).then(setValues).catch(() => {}); }
  useEffect(load, [dim]);

  async function add() {
    const clean = newName.trim();
    if (!clean) return;
    setNewName("");
    await createLabel(dim, clean).catch(() => {});
    load();
  }
  async function rename(id: string, name: string) {
    const res = await renameLabel(dim, id, name).catch(() => null);
    if (res?.merged) { setMsg("Se fusionó con una etiqueta existente ✓"); setTimeout(() => setMsg(""), 2600); }
    load();
  }
  async function remove(v: LabelValue) {
    const extra = v.count ? ` (${v.count} reels quedan sin ${label.toLowerCase()})` : "";
    if (!window.confirm(`¿Borrar "${v.name}"?${extra}`)) return;
    await deleteLabel(dim, v.id).catch(() => {});
    load();
  }

  return (
    <section className="card label-card">
      <h3 className="card-title">{label}</h3>
      <div className="label-add">
        <input value={newName} onChange={(e) => setNewName(e.target.value)}
               onKeyDown={(e) => e.key === "Enter" && add()}
               placeholder={`Nuevo valor…`} />
        <button className="btn btn-primary" onClick={add}>Agregar</button>
      </div>
      {msg && <p className="sync-msg">{msg}</p>}
      <ul className="label-list">
        {values.map((v) => (
          <LabelRow key={v.id} v={v} onRename={(n) => rename(v.id, n)} onDelete={() => remove(v)} />
        ))}
        {values.length === 0 && <li className="label-empty">Sin valores todavía</li>}
      </ul>
    </section>
  );
}

export default function EtiquetasPage() {
  const [seedKey, setSeedKey] = useState(0);
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState("");

  async function loadSuggested() {
    setSeeding(true);
    try {
      await seedDefaultLabels();
      setSeedKey((k) => k + 1);  // remonta los managers → recargan
      setSeedMsg("Valores sugeridos cargados ✓");
    } catch {
      setSeedMsg("No se pudieron cargar");
    }
    setSeeding(false);
    setTimeout(() => setSeedMsg(""), 3000);
  }

  return (
    <div className="labels-wrap">
      <div className="labels-head">
        <h1 className="page-title">Etiquetas</h1>
        <div className="labels-head-actions">
          {seedMsg && <span className="sync-msg">{seedMsg}</span>}
          <button className="btn btn-ghost" onClick={loadSuggested} disabled={seeding}>
            {seeding ? "Cargando…" : "Cargar valores sugeridos"}
          </button>
        </div>
      </div>
      <p className="hint labels-intro">
        Gestioná los valores de cada dimensión. Click en un nombre para <b>renombrar</b>, la ✕ para <b>borrar</b>,
        o "Agregar" para sumar uno nuevo. No distingue mayúsculas y si renombrás uno al nombre de otro que ya
        existe, <b>se fusionan</b> (así no se duplican por tipeo). "Cargar valores sugeridos" trae los comunes del
        framework de contenido — después los editás a gusto.
      </p>
      <div className="labels-grid">
        {DIMENSIONS.map(({ key, label }) => (
          <DimensionManager key={`${key}-${seedKey}`} dim={key} label={label} />
        ))}
      </div>
    </div>
  );
}
