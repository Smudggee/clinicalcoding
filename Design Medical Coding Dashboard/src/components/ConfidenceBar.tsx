interface Props {
  value: number; // 0-100
  animated?: boolean;
}

export default function ConfidenceBar({ value, animated = true }: Props) {
  const color =
    value >= 80 ? "#16A34A" : value >= 50 ? "#EA580C" : "#DC2626";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={animated ? "confidence-bar-fill" : ""}
          style={{
            height: "100%",
            width: `${value}%`,
            background: color,
            borderRadius: "999px",
            transformOrigin: "left",
          }}
        />
      </div>
      <span
        className="text-xs font-semibold tabular-nums"
        style={{ color, minWidth: "2.5rem", textAlign: "right" }}
      >
        {value}%
      </span>
    </div>
  );
}
