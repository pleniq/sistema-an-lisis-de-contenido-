import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSyncStatus, triggerRefresh, SyncStatus } from "./api";

const STALE_MS = 5 * 60 * 1000;

function isStale(lastSyncedAt: string | null): boolean {
  if (!lastSyncedAt) return true;
  return Date.now() - new Date(lastSyncedAt).getTime() > STALE_MS;
}

/**
 * Maneja el sync on-demand: al montar, si los datos están viejos y n8n está vivo,
 * dispara una actualización; deja un botón manual y pollea el estado mientras corre.
 * `onSynced` se llama cuando una corrida termina, para recargar los datos.
 */
export function useSync(onSynced: () => void) {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<string>("");
  const pollRef = useRef<number | null>(null);
  const onSyncedRef = useRef(onSynced);
  onSyncedRef.current = onSynced;

  const stopPolling = useCallback(() => {
    if (pollRef.current !== null) { window.clearInterval(pollRef.current); pollRef.current = null; }
  }, []);

  const startPolling = useCallback(() => {
    stopPolling();
    pollRef.current = window.setInterval(async () => {
      const s = await fetchSyncStatus().catch(() => null);
      if (!s) return;
      setStatus(s);
      if (!s.running) {
        stopPolling();
        setSyncing(false);
        setMessage("");
        onSyncedRef.current();
      }
    }, 2000);
  }, [stopPolling]);

  const refresh = useCallback(async (force: boolean) => {
    setSyncing(true);
    setMessage("Actualizando…");
    const code = await triggerRefresh(force).catch(() => 0);
    if (code === 202 || code === 409) {
      startPolling();
    } else {
      setSyncing(false);
      if (code === 503) setMessage("n8n apagado");
      else if (code === 200) setMessage("");
      else setMessage("No se pudo disparar la actualización");
      const s = await fetchSyncStatus().catch(() => null);
      if (s) setStatus(s);
    }
  }, [startPolling]);

  useEffect(() => {
    let active = true;
    (async () => {
      const s = await fetchSyncStatus().catch(() => null);
      if (!active) return;
      setStatus(s);
      if (s && s.n8n_alive && !s.running && isStale(s.last_synced_at)) {
        refresh(false);
      } else if (s && s.running) {
        setSyncing(true);
        startPolling();
      }
    })();
    return () => { active = false; stopPolling(); };
  }, [refresh, startPolling, stopPolling]);

  return { status, syncing, message, refresh };
}
