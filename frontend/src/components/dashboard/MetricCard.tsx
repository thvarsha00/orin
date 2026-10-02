import type { LucideIcon } from "lucide-react";

export type MetricState = "ok" | "loading" | "soon" | "error";

export function MetricCard({ icon: Icon, label, value, caption, state = "ok" }: {
  icon: LucideIcon; label: string; value?: string | number; caption?: string; state?: MetricState;
}) {
  return (
    <div className="surface surface-hover p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{label}</span>
        <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent/10 text-accent"><Icon size={16} /></span>
      </div>
      <div className="mt-3">
        {state === "loading" && <div className="h-7 w-16 animate-pulse rounded bg-white/10" />}
        {state === "ok" && <p className="text-2xl font-semibold tracking-tight">{value}</p>}
        {state === "soon" && <p className="text-sm text-slate-500">Not available yet</p>}
        {state === "error" && <p className="text-sm text-slate-500">Couldn't load</p>}
      </div>
      {state === "ok" && caption && <p className="mt-1 text-xs text-slate-500">{caption}</p>}
    </div>
  );
}
