import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

export function EmptyState({ icon: Icon, title, text, actionLabel, to }: {
  icon: LucideIcon; title: string; text: string; actionLabel?: string; to?: string;
}) {
  return (
    <div className="flex flex-col items-center px-4 py-8 text-center">
      <span className="grid h-11 w-11 place-items-center rounded-xl bg-accent/10 text-accent"><Icon size={20} /></span>
      <p className="mt-4 font-medium">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-slate-400">{text}</p>
      {actionLabel && to && (
        <Link to={to} className="mt-5 rounded-lg border border-line px-4 py-2 text-sm font-medium transition-colors hover:border-accent/50 hover:bg-accent/10">
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
