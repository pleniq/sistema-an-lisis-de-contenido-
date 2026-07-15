import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { DIMENSIONS, Dimension, LabelValue, ReelRow, fetchReels, fetchLabels } from "./lib/api";
import { AppContext } from "./lib/appContext";
import { useSync } from "./lib/useSync";
import SyncBar from "./components/SyncBar";

const EMPTY_LABELS: Record<Dimension, LabelValue[]> = {
  angulo: [], formato: [], tipo_hook: [], categoria: [], tema: [],
};

export default function App() {
  const [reels, setReels] = useState<ReelRow[]>([]);
  const [labelOptions, setLabelOptions] = useState<Record<Dimension, LabelValue[]>>(EMPTY_LABELS);
  const [error, setError] = useState<string | null>(null);

  const reloadReels = useCallback(() => {
    fetchReels().then(setReels).catch((e) => setError(e.message));
  }, []);

  const reloadLabels = useCallback(() => {
    Promise.all(DIMENSIONS.map(({ key }) => fetchLabels(key).then((vals) => [key, vals] as const)))
      .then((pairs) => setLabelOptions(Object.fromEntries(pairs) as Record<Dimension, LabelValue[]>))
      .catch(() => {});
  }, []);

  const updateReel = useCallback((updated: ReelRow) => {
    setReels((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
  }, []);

  const { status, syncing, message, refresh } = useSync(reloadReels);

  useEffect(() => { reloadReels(); reloadLabels(); }, [reloadReels, reloadLabels]);

  const ctx: AppContext = { reels, reloadReels, labelOptions, reloadLabels, updateReel };

  return (
    <div className="wrap">
      <header className="topbar">
        <div className="brand">
          <h1>Laboratorio de Contenido</h1>
          <nav className="nav">
            <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>Tabla</NavLink>
            <NavLink to="/analisis" className={({ isActive }) => (isActive ? "active" : "")}>Qué funciona</NavLink>
          </nav>
        </div>
        <SyncBar status={status} syncing={syncing} message={message} onRefresh={() => refresh(true)} />
      </header>
      {error && <p style={{ color: "crimson" }}>Error: {error}</p>}
      <Outlet context={ctx} />
    </div>
  );
}
