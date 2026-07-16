import { useEffect, useState } from "react";
import { fetchMetaConfig, saveMetaConfig, triggerRefresh, MetaConfigStatus } from "../lib/api";

export default function ConfigPage() {
  const [status, setStatus] = useState<MetaConfigStatus | null>(null);
  const [token, setToken] = useState("");
  const [igUserId, setIgUserId] = useState("");
  const [appId, setAppId] = useState("");
  const [appSecret, setAppSecret] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  function load() {
    fetchMetaConfig().then((s) => {
      setStatus(s);
      if (s.ig_user_id) setIgUserId(s.ig_user_id);
    }).catch(() => {});
  }
  useEffect(load, []);

  async function save(sync: boolean) {
    if (!token.trim()) { setMsg("Pegá el token de acceso."); return; }
    setBusy(true);
    setMsg("Guardando…");
    try {
      const s = await saveMetaConfig({
        access_token: token.trim(),
        ig_user_id: igUserId.trim() || undefined,
        app_id: appId.trim() || undefined,
        app_secret: appSecret.trim() || undefined,
      });
      setStatus(s);
      if (s.token_status === "ok") {
        setToken(""); setAppSecret("");
        if (sync) {
          setMsg("Token guardado. Sincronizando tus reels…");
          const res = await triggerRefresh(true);
          setMsg(res.outcome === "ok" ? `Listo · ${res.reels_processed} reels sincronizados` : `Guardado (sync: ${res.outcome})`);
        } else {
          setMsg("Token guardado ✓");
        }
      } else {
        setMsg(s.last_error || "El token no funcionó.");
      }
    } catch {
      setMsg("Error al guardar.");
    }
    setBusy(false);
  }

  const st = status?.token_status;
  const badge =
    st === "ok" ? <span className="chip chip-ok">Conectado</span>
    : st === "expired" ? <span className="chip chip-err">Token expirado</span>
    : <span className="chip chip-warn">Sin conectar</span>;

  return (
    <div className="config-wrap">
      <h1 className="page-title">Configuración de Meta</h1>

      <section className="card config-status">
        <div className="config-status-head">
          {badge}
          {status?.account_name && <span className="muted">Cuenta: <b>{status.account_name}</b></span>}
        </div>
        <div className="config-status-body">
          {status?.ig_user_id && <div><span className="muted">IG User ID</span><code>{status.ig_user_id}</code></div>}
          {status?.long_lived && status?.days_left != null && (
            <div><span className="muted">Vencimiento</span><b>{status.days_left} días</b></div>
          )}
          {st === "expired" && <p className="err-text">El token expiró. Generá uno nuevo y pegalo abajo.</p>}
          {status?.last_error && st !== "ok" && <p className="err-text">{status.last_error}</p>}
        </div>
      </section>

      <section className="card config-form">
        <h2 className="card-title">Conectar / actualizar token</h2>
        <div className="field">
          <label>Token de acceso <span className="req">*</span></label>
          <textarea rows={3} value={token} onChange={(e) => setToken(e.target.value)}
                    placeholder="EAAG… (pegá el token del Graph API Explorer)" />
        </div>
        <div className="field">
          <label>IG User ID</label>
          <input value={igUserId} onChange={(e) => setIgUserId(e.target.value)} placeholder="178414…" />
        </div>
        <div className="field-row">
          <div className="field">
            <label>App ID <span className="muted">(para token de 60 días)</span></label>
            <input value={appId} onChange={(e) => setAppId(e.target.value)} placeholder="opcional" />
          </div>
          <div className="field">
            <label>App Secret <span className="muted">(para token de 60 días)</span></label>
            <input type="password" value={appSecret} onChange={(e) => setAppSecret(e.target.value)} placeholder="opcional" />
          </div>
        </div>

        <div className="panel-actions">
          <button className="btn btn-primary" onClick={() => save(true)} disabled={busy}>
            {busy ? "Procesando…" : "Guardar y sincronizar"}
          </button>
          <button className="btn btn-ghost" onClick={() => save(false)} disabled={busy}>Solo guardar</button>
          {msg && <span className="sync-msg">{msg}</span>}
        </div>

        <p className="hint">
          El token se guarda en el sistema y toma efecto al instante — no hace falta reiniciar nada.
          Si cargás <b>App ID</b> + <b>App Secret</b>, se convierte automáticamente en un token de <b>~60 días</b>.
          Cuando venza, el sistema te avisa acá y pegás uno nuevo.
        </p>
      </section>
    </div>
  );
}
