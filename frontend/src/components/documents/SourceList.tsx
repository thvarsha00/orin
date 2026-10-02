import { useState } from "react";
import { ExternalLink } from "lucide-react";
import { openDocument } from "../../services/api";
import type { DocSource } from "../../types";

export function SourceList({ sources, exists }: { sources: DocSource[]; exists: (documentId: number) => boolean }) {
  const [error, setError] = useState("");
  if (sources.length === 0) return null;

  const view = async (s: DocSource) => {
    setError("");
    try { await openDocument(s.document_id, s.page_number); }
    catch (e) { setError((e as Error).message); }
  };

  return (
    <div className="mt-4 rounded-xl border border-line bg-white/[0.02] p-3.5">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Sources</p>
      <ul className="mt-2 space-y-2.5">
        {sources.map((s) => (
          <li key={`${s.document_id}-${s.page_number ?? "x"}`} className="text-sm">
            <div className="flex items-center justify-between gap-3">
              <p className="min-w-0 truncate text-slate-200">
                {s.document_name}{s.page_number ? <span className="text-slate-400"> · Page {s.page_number}</span> : null}
              </p>
              {exists(s.document_id) && (
                <button onClick={() => view(s)} className="flex shrink-0 items-center gap-1 text-xs text-accent2 hover:text-white">
                  View source <ExternalLink size={12} />
                </button>
              )}
            </div>
            <p className="mt-0.5 line-clamp-2 text-xs leading-relaxed text-slate-500">{s.snippet}</p>
          </li>
        ))}
      </ul>
      {error && <p className="mt-2 text-xs text-red-300">{error}</p>}
    </div>
  );
}
