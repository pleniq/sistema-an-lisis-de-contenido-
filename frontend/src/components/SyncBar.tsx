import { Link } from "react-router-dom";
import { SyncStatus } from "../lib/api";

interface Props {
  status: SyncStatus | null;
  syncing: boolean;
  message: string;
  onRefresh: () => void;
}

function fmtTime(iso: string | null): string {
  if (!iso) return "nunca";
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
  });
}

export default function SyncBar({ status, syncing, message, onRefresh }: Props) {
  const running = syncing || status?.running;
  const token = status?.token_status;

  let chip;
  if (running) chip = <span className="chip chip-run">Actualizando…</span>;
  else if (!status || token === "missing") chip = <Link to="/config" className="chip chip-warn">Sin configurar</Link>;
  else if (token === "expired") chip = <Link to="/config" className="chip chip-err">Token expirado · reconectar</Link>;
  else chip = <span className="chip chip-ok">Al día</span>;

  const canRefresh = token === "ok" && !running;

  return (
    <div className="syncbar">
      {chip}
      <span className="sync-meta">Últ. sync {fmtTime(status?.last_synced_at ?? null)}</span>
      {message && <span className="sync-msg">{message}</span>}
      <button className="btn btn-primary" onClick={onRefresh} disabled={!canRefresh}>
        {running ? "Actualizando…" : "Actualizar"}
      </button>
    </div>
  );
}
