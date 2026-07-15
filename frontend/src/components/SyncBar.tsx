import { SyncStatus } from "../lib/api";

interface Props {
  status: SyncStatus | null;
  syncing: boolean;
  message: string;
  onRefresh: () => void;
}

function fmtTime(iso: string | null): string {
  if (!iso) return "nunca";
  const d = new Date(iso);
  return d.toLocaleString("es-AR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export default function SyncBar({ status, syncing, message, onRefresh }: Props) {
  const running = syncing || status?.running;
  const n8nDown = status != null && !status.n8n_alive;

  let chipText: string;
  let chipClass: string;
  if (running) { chipText = "Actualizando…"; chipClass = "chip chip-run"; }
  else if (n8nDown) { chipText = "n8n apagado"; chipClass = "chip chip-off"; }
  else { chipText = "Al día"; chipClass = "chip chip-ok"; }

  return (
    <div className="syncbar">
      <span className={chipClass}>{chipText}</span>
      <span className="sync-meta">Último sync: {fmtTime(status?.last_synced_at ?? null)}</span>
      {message && <span className="sync-msg">{message}</span>}
      <button className="btn" onClick={onRefresh} disabled={!!running || n8nDown}>
        {running ? "Actualizando…" : "Actualizar"}
      </button>
    </div>
  );
}
