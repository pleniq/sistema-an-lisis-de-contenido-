import { useCallback, useEffect, useRef, useState } from "react";
import { fetchSyncStatus, triggerRefresh, SyncStatus, RefreshResult } from "./api";

const STALE_MS = 5 * 60 * 1000;

function isStale(lastSyncedAt: string | null): boolean {
  if (!lastSyncedAt) return true;
  return Date.now() - new Date(lastSyncedAt).getTime() > STALE_MS;
}

/**
 * Sync on-demand. El backend jala directo de Meta (sincrónico), así que refresh()
 * espera el resultado y recarga. Al abrir, si los datos están viejos y el token está
 * ok, actualiza solo. Expone el estado del token para avisar "expirado".
 */
export function useSync(onSynced: () => void) {
  const [status, setStatus] = useState<SyncStatus | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState("");
  const onSyncedRef = useRef(onSynced);
  onSyncedRef.current = onSynced;

  const loadStatus = useCallback(async () => {
    const s = await fetchSyncStatus().catch(() => null);
    if (s) setStatus(s);
    return s;
  }, []);

  const refresh = useCallback(async (force: boolean) => {
    setSyncing(true);
    setMessage("");
    const res: RefreshResult = await triggerRefresh(force).catch(() => ({ outcome: "error" }));
    switch (res.outcome) {
      case "ok":
        setMessage(`Actualizado · ${res.reels_processed ?? ""} reels`);
        onSyncedRef.current();
        break;
      case "token_expired": setMessage("Token de Meta expirado"); break;
      case "not_configured": setMessage("Falta el token en Configuración"); break;
      case "already_running": setMessage("Ya se está actualizando"); break;
      case "error": setMessage("No se pudo actualizar"); break;
      default: break; // skipped_fresh → sin mensaje
    }
    await loadStatus();
    setSyncing(false);
  }, [loadStatus]);

  useEffect(() => {
    let active = true;
    (async () => {
      const s = await loadStatus();
      if (!active || !s) return;
      if (s.configured && s.token_status === "ok" && !s.running && isStale(s.last_synced_at)) {
        refresh(false);
      }
    })();
    return () => { active = false; };
  }, [loadStatus, refresh]);

  return { status, syncing, message, refresh, reloadStatus: loadStatus };
}
