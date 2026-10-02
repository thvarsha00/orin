import type { ScriptPref } from "../types";

export function ScriptSelect({ value, onChange, compact = false }: { value: ScriptPref; onChange: (s: ScriptPref) => void; compact?: boolean }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value as ScriptPref)} aria-label="Response script"
      title="How Orin writes your language: match your style, Roman letters, or native script"
      className={`border border-line bg-panel outline-none focus:border-accent ${compact ? "h-8 rounded-lg bg-white/5 px-2 text-xs" : "rounded-md px-2 py-1.5 text-sm"}`}>
      <option value="auto">Match my preference</option>
      <option value="roman">Romanized</option>
      <option value="native">Native script</option>
    </select>
  );
}
