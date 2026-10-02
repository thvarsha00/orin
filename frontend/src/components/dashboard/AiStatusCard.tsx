import { Cpu, RefreshCw } from "lucide-react";
import type { Health } from "../../types";

type Status = "ready" | "connecting" | "unavailable";

function statusOf(health: Health | null, error: string): Status {
  if (error) return "unavailable";
  if (!health) return "connecting";
  return health.ai.reachable && health.ai.chat_model_available ? "ready" : "unavailable";
}

const STYLE: Record<Status, { label: string; dot: string; text: string }> = {
  ready: { label: "Ready", dot: "bg-emerald-400", text: "text-emerald-400" },
  connecting: { label: "Connecting", dot: "bg-amber-400 animate-pulse", text: "text-amber-400" },
  unavailable: { label: "Unavailable", dot: "bg-red-400", text: "text-red-400" },
};

export function AiStatusCard({ health, error, onRetry }: { health: Health | null; error: string; onRetry: () => void }) {
  const status = statusOf(health, error);
  const s = STYLE[status];
  const ai = health?.ai;
  const detail = error || (status === "unavailable" ? ai?.hint : null);

  return (
    <section className="surface flex flex-col p-5" aria-live="polite">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-medium text-slate-300"><Cpu size={16} className="text-accent" /> AI system</h2>
        <span className={`flex items-center gap-2 rounded-full bg-white/5 px-2.5 py-1 text-xs font-medium ${s.text}`}>
          <span className={`h-2 w-2 rounded-full ${s.dot}`} /> {s.label}
        </span>
      </div>

      <dl className="mt-5 space-y-3 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Provider</dt>
          <dd className="truncate">{ai ? ai.provider : <span className="inline-block h-4 w-20 animate-pulse rounded bg-white/10 align-middle" />}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Model</dt>
          <dd className="truncate">{ai ? ai.chat_model : <span className="inline-block h-4 w-28 animate-pulse rounded bg-white/10 align-middle" />}</dd>
        </div>
      </dl>

      {detail && <p className="mt-4 text-xs leading-relaxed text-slate-400">{detail}</p>}
      {status === "unavailable" && (
        <button onClick={onRetry} className="mt-auto flex w-fit items-center gap-2 pt-4 text-xs text-accent2 hover:text-white">
          <RefreshCw size={12} /> Check again
        </button>
      )}
    </section>
  );
}
