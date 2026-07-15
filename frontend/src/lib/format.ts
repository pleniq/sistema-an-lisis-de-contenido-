export const num = (v: number | null) => (v == null ? "—" : Math.round(v).toLocaleString("es-AR"));
export const pct = (v: number | null) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
export const sec = (v: number | null) => (v == null ? "—" : v.toFixed(1));
export const day = (iso: string | null) => (iso ? iso.slice(0, 10) : "—");
