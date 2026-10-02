import { useState } from "react";
import { Link } from "react-router-dom";
import { Eye, FileText, MessageSquare, RotateCw, Trash2 } from "lucide-react";
import { formatDate, formatSize, isBusy, TYPE_LABEL } from "../../lib/documents";
import type { DocumentItem } from "../../types";
import { StatusBadge } from "./StatusBadge";

interface Props {
  doc: DocumentItem;
  onView: (d: DocumentItem) => void;
  onRetry: (d: DocumentItem) => void;
  onDelete: (d: DocumentItem) => void;
}

const btn = "inline-flex items-center gap-1.5 rounded-lg border border-line px-3 py-1.5 text-xs font-medium text-slate-200 transition-colors hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40";

export function DocumentCard({ doc, onView, onRetry, onDelete }: Props) {
  const [confirming, setConfirming] = useState(false);
  const ready = doc.status === "ready";
  const meta = [TYPE_LABEL[doc.file_type], formatSize(doc.file_size),
    doc.page_count ? `${doc.page_count} ${doc.page_count === 1 ? "page" : "pages"}` : null,
    ready ? `${doc.chunk_count} chunks` : null].filter(Boolean);

  return (
    <article className="surface surface-hover flex flex-col p-5">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-accent/10 text-accent"><FileText size={20} /></span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-medium" title={doc.filename}>{doc.filename}</h3>
          <p className="mt-0.5 text-xs text-slate-500">{meta.join(" · ")}</p>
          <p className="text-xs text-slate-500">Uploaded {formatDate(doc.created_at)}</p>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <StatusBadge doc={doc} />
        {isBusy(doc) && (
          <div className="space-y-1.5" aria-live="polite">
            <div className="indeterminate h-1.5 rounded-full bg-white/10" />
            <p className="text-xs text-slate-500">This can take a minute for longer documents.</p>
          </div>
        )}
        {doc.status === "failed" && (
          <div>
            <p className="text-sm font-medium text-red-300">Processing failed</p>
            {doc.error && <p className="mt-0.5 text-xs leading-relaxed text-slate-400">{doc.error}</p>}
          </div>
        )}
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-2">
        {ready && (
          <Link to={`/documents/${doc.id}/ask`}
            className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white transition hover:brightness-110">
            <MessageSquare size={13} /> Ask Questions
          </Link>
        )}
        {ready && <button className={btn} onClick={() => onView(doc)}><Eye size={13} /> View</button>}
        {doc.status === "failed" && <button className={btn} onClick={() => onRetry(doc)}><RotateCw size={13} /> Retry</button>}
        {confirming ? (
          <span className="ml-auto flex items-center gap-2 text-xs">
            <span className="text-slate-400">Delete?</span>
            <button className="rounded-lg bg-red-500/80 px-2.5 py-1.5 font-medium text-white hover:bg-red-500" onClick={() => onDelete(doc)}>Delete</button>
            <button className={btn} onClick={() => setConfirming(false)}>Cancel</button>
          </span>
        ) : (
          <button className={`${btn} ml-auto hover:border-red-400/40 hover:text-red-300`} onClick={() => setConfirming(true)}
            aria-label={`Delete ${doc.filename}`}><Trash2 size={13} /> Delete</button>
        )}
      </div>
    </article>
  );
}
