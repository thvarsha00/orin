const STYLE: Record<string, string> = {
  easy: "bg-emerald-500/15 text-emerald-300",
  medium: "bg-amber-500/15 text-amber-300",
  hard: "bg-rose-500/15 text-rose-300",
};

export function DifficultyBadge({ level }: { level: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${STYLE[level] ?? "bg-white/10 text-slate-300"}`}>
      {level}
    </span>
  );
}
