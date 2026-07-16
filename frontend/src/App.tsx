import { useCallback, useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { DIMENSIONS, Dimension, LabelValue, ReelRow, fetchReels, fetchLabels } from "./lib/api";
import { AppContext } from "./lib/appContext";
import { useSync } from "./lib/useSync";
import SyncBar from "./components/SyncBar";

const EMPTY_LABELS: Record<Dimension, LabelValue[]> = {
  angulo: [], formato: [], tipo_hook: [], categoria: [], tema: [],
};

const navClass = ({ isActive }: { isActive: boolean }) => (isActive ? "nav-link active" : "nav-link");

export default function App() {
  const [reels, setReels] = useState<ReelRow[]>([]);
  const [labelOptions, setLabelOptions] = useState<Record<Dimension, LabelValue[]>>(EMPTY_LABELS);

  const reloadReels = useCallback(() => { fetchReels().then(setReels).catch(() => {}); }, []);

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
    <div className="app">
      <header className="topbar">
        <div className="topbar-left">
          <div className="logo">
            <span className="logo-mark" aria-hidden />
            <span className="logo-text">Laboratorio de Contenido</span>
          </div>
          <nav className="nav">
            <NavLink to="/" end className={navClass}>Publicaciones</NavLink>
            <NavLink to="/analisis" className={navClass}>Qué funciona</NavLink>
            <NavLink to="/etiquetas" className={navClass}>Etiquetas</NavLink>
            <NavLink to="/config" className={navClass}>Configuración</NavLink>
          </nav>
        </div>
        <SyncBar status={status} syncing={syncing} message={message} onRefresh={() => refresh(true)} />
      </header>
      <main className="content">
        <Outlet context={ctx} />
      </main>
    </div>
  );
}
