interface Props {
  values: (number | null)[];
  width?: number;
  height?: number;
  stroke?: string;
}

/** Mini-gráfico de línea, sin librerías externas (SVG inline). */
export default function Sparkline({ values, width = 240, height = 44, stroke = "#111" }: Props) {
  const nums = values.map((v) => v ?? 0);
  if (nums.length === 0) return <span className="tag">sin datos</span>;

  const max = Math.max(...nums);
  const min = Math.min(...nums);
  const range = max - min || 1;
  const y = (v: number) => height - ((v - min) / range) * (height - 6) - 3;

  if (nums.length === 1) {
    return (
      <svg width={width} height={height}>
        <circle cx={4} cy={y(nums[0])} r={3} fill={stroke} />
      </svg>
    );
  }

  const step = width / (nums.length - 1);
  const pts = nums.map((v, i) => `${i * step},${y(v)}`).join(" ");
  return (
    <svg width={width} height={height}>
      <polyline points={pts} fill="none" stroke={stroke} strokeWidth={2} />
      {nums.map((v, i) => <circle key={i} cx={i * step} cy={y(v)} r={2} fill={stroke} />)}
    </svg>
  );
}
