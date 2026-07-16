import { KeyboardEvent, useEffect, useRef, useState } from "react";
import { LabelValue } from "../lib/api";

interface Props {
  value: string;
  options: LabelValue[];
  onChange: (v: string) => void;
  onCreate?: (name: string) => void;  // crea la etiqueta al instante y la suma a la lista
  placeholder?: string;
}

type Item =
  | { kind: "option"; name: string; count?: number }
  | { kind: "create"; name: string };

/**
 * Selector de etiqueta: al enfocar muestra las opciones ya creadas, filtra
 * mientras escribís, y si el texto no existe ofrece "＋ Crear «…»".
 * Navegable con flechas + Enter + Escape.
 */
export default function LabelCombobox({ value, options, onChange, onCreate, placeholder }: Props) {
  const [open, setOpen] = useState(false);
  const [hi, setHi] = useState(-1);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const q = value.trim().toLowerCase();
  const filtered = options.filter((o) => o.name.toLowerCase().includes(q));
  const exact = options.some((o) => o.name.toLowerCase() === q);
  const showCreate = value.trim() !== "" && !exact;

  const items: Item[] = [
    ...filtered.map((o) => ({ kind: "option" as const, name: o.name, count: o.count })),
    ...(showCreate ? [{ kind: "create" as const, name: value.trim() }] : []),
  ];

  function choose(item: Item) {
    if (item.kind === "create") onCreate?.(item.name);
    onChange(item.name);
    setOpen(false);
    setHi(-1);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!open && (e.key === "ArrowDown" || e.key === "Enter")) { setOpen(true); return; }
    if (e.key === "ArrowDown") { e.preventDefault(); setHi((h) => Math.min(h + 1, items.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setHi((h) => Math.max(h - 1, 0)); }
    else if (e.key === "Enter") {
      if (hi >= 0 && hi < items.length) { e.preventDefault(); choose(items[hi]); }
      else setOpen(false);
    } else if (e.key === "Escape") { setOpen(false); setHi(-1); }
  }

  return (
    <div className="combo" ref={ref}>
      <input
        value={value}
        onChange={(e) => { onChange(e.target.value); setOpen(true); setHi(-1); }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        placeholder={placeholder}
      />
      {open && items.length > 0 && (
        <ul className="combo-menu">
          {items.map((it, i) => (
            <li
              key={`${it.kind}-${it.name}`}
              className={`combo-item ${it.kind === "create" ? "combo-create" : ""} ${i === hi ? "hl" : ""}`}
              onMouseEnter={() => setHi(i)}
              onMouseDown={() => choose(it)}
            >
              {it.kind === "create" ? (
                `＋ Crear «${it.name}»`
              ) : (
                <>
                  <span>{it.name}</span>
                  {it.count ? <span className="combo-count">{it.count}</span> : null}
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
