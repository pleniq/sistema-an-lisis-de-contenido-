import { useEffect, useRef, useState } from "react";
import { LabelValue } from "../lib/api";

interface Props {
  value: string;
  options: LabelValue[];
  onChange: (v: string) => void;
  onCreate?: (name: string) => void;  // crea la etiqueta al instante y la suma a la lista
  placeholder?: string;
}

/**
 * Selector de etiqueta: al enfocar muestra las opciones ya creadas, filtra
 * mientras escribís, y si el texto no existe ofrece "＋ Crear «…»".
 */
export default function LabelCombobox({ value, options, onChange, onCreate, placeholder }: Props) {
  const [open, setOpen] = useState(false);
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

  return (
    <div className="combo" ref={ref}>
      <input
        value={value}
        onChange={(e) => { onChange(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        placeholder={placeholder}
      />
      {open && (filtered.length > 0 || showCreate) && (
        <ul className="combo-menu">
          {filtered.map((o) => (
            <li key={o.id} className="combo-item"
                onMouseDown={() => { onChange(o.name); setOpen(false); }}>
              <span>{o.name}</span>
              {o.count ? <span className="combo-count">{o.count}</span> : null}
            </li>
          ))}
          {showCreate && (
            <li className="combo-item combo-create"
                onMouseDown={() => {
                  const name = value.trim();
                  onCreate?.(name);   // lo crea y lo suma a la lista al instante
                  onChange(name);
                  setOpen(false);
                }}>
              ＋ Crear «{value.trim()}»
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
