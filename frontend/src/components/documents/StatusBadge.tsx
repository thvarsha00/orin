import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { isBusy, STATUS_LABEL } from "../../lib/documents";
import type { DocumentItem } from "../../types";

export function StatusBadge({ doc }: { doc: DocumentItem }) {
  const tone = doc.status === "ready" ? "text-emerald-400" : doc.status === "failed" ? "text-red-400" : "text-amber-300";
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full bg-white/5 px-2.5 py-1 text-xs font-medium ${tone}`} role="status">
      {doc.status === "ready" && <CheckCircle2 size={13} />}
      {doc.status === "failed" && <AlertCircle size={13} />}
      {isBusy(doc) && <Loader2 size={13} className="animate-spin" />}
      {STATUS_LABEL[doc.status]}
    </span>
  );
}
