import { Languages } from "lucide-react";
import { LANGUAGES } from "../lib/languages";
import type { Language } from "../types";

export function LanguageSelect({ value, onChange, compact = false }: { value: Language; onChange: (l: Language) => void; compact?: boolean }) {
  return (
    <label className={`flex items-center gap-2 text-slate-300 ${compact ? "text-xs" : "text-sm"}`} title="Language Orin explains in">
      <Languages size={compact ? 14 : 16} className="text-accent2" />
      <select value={value} onChange={(e) => onChange(e.target.value as Language)} aria-label="Language"
        className={`border border-line bg-panel text-slate-100 outline-none focus:border-accent ${compact ? "h-8 rounded-lg px-2" : "rounded-md px-2 py-1.5"}`}>
        {LANGUAGES.map((l) => (
          <option key={l.code} value={l.code}>{l.native === l.label ? l.label : `${l.native} (${l.label})`}</option>
        ))}
      </select>
    </label>
  );
}