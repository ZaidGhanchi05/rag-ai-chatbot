/**
 * ConfidenceBar component
 * Visual progress bar showing retrieval confidence score.
 * Color: red (< 0.4) → amber (< 0.65) → green (≥ 0.65)
 */
export default function ConfidenceBar({ confidence }) {
  if (confidence === null || confidence === undefined) return null;

  const pct = Math.round(confidence * 100);

  const color =
    confidence < 0.4
      ? { bar: "bg-red-500", text: "text-red-400", label: "Low" }
      : confidence < 0.65
      ? { bar: "bg-amber-400", text: "text-amber-400", label: "Medium" }
      : { bar: "bg-cyan-400", text: "text-cyan-400", label: "High" };

  return (
    <div className="confidence-bar-wrap">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500">Confidence</span>
        <span className={`text-xs font-semibold ${color.text}`}>
          {color.label} · {pct}%
        </span>
      </div>
      <div className="confidence-track">
        <div
          className={`confidence-fill ${color.bar}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
