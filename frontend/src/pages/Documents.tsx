import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertCircle, FileText, Library, RefreshCw, Search, Upload } from "lucide-react";
import { DocumentCard } from "../components/documents/DocumentCard";
import { UploadZone } from "../components/documents/UploadZone";
import { isBusy } from "../lib/documents";
import { api, openDocument } from "../services/api";
import type { DocumentItem, DocumentsConfig } from "../types";

type Filter = "all" | "ready" | "processing" | "failed";
type Sort = "newest" | "oldest" | "name";
const POLL_MS = 2000;

const field = "h-9 rounded-lg border border-line bg-panel px-3 text-sm text-slate-100 outline-none focus:border-accent";

export default function Documents() {
  const [docs, setDocs] = useState<DocumentItem[] | null>(null);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [config, setConfig] = useState<DocumentsConfig | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [sort, setSort] = useState<Sort>("newest");

  const load = useCallback(() => {
    return api<DocumentItem[]>("/documents").then((d) => { setDocs(d); setLoadError(""); })
      .catch((e: Error) => setLoadError(e.message));
  }, []);
  const loadConfig = useCallback(() => { api<DocumentsConfig>("/documents/config").then(setConfig).catch(() => {}); }, []);
  useEffect(() => { void load(); loadConfig(); }, [load, loadConfig]);

  // Poll only while something is processing; stops by itself once every document has settled.
  const anyBusy = docs?.some(isBusy) ?? false;
  useEffect(() => {
    if (!anyBusy) return;
    const t = setTimeout(() => { void load(); }, POLL_MS);
    return () => clearTimeout(t);
  }, [anyBusy, docs, load]);

  const replace = (d: DocumentItem) => setDocs((list) => (list ?? []).map((x) => (x.id === d.id ? d : x)));
  const onUploaded = useCallback((d: DocumentItem) => setDocs((list) => [d, ...(list ?? []).filter((x) => x.id !== d.id)]), []);

  const guard = async (fn: () => Promise<void>) => { setActionError(""); try { await fn(); } catch (e) { setActionError((e as Error).message); } };
  const onView = (d: DocumentItem) => guard(() => openDocument(d.id));
  const onRetry = (d: DocumentItem) => guard(async () => replace(await api<DocumentItem>(`/documents/${d.id}/retry`, "POST")));
  const onDelete = (d: DocumentItem) => guard(async () => {
    await api(`/documents/${d.id}`, "DELETE");
    setDocs((list) => (list ?? []).filter((x) => x.id !== d.id));
  });

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (docs ?? []).filter((d) =>
      (!q || d.filename.toLowerCase().includes(q)) &&
      (filter === "all" || (filter === "processing" ? isBusy(d) : d.status === filter)));
    return list.sort((a, b) => sort === "name" ? a.filename.localeCompare(b.filename)
      : sort === "oldest" ? a.id - b.id : b.id - a.id);
  }, [docs, query, filter, sort]);

  const readyCount = docs?.filter((d) => d.status === "ready").length ?? 0;
  const showUpload = uploadOpen || docs?.length === 0;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-5 md:p-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Documents</h1>
          <p className="mt-1 text-slate-300">Upload your study materials and learn directly from them.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {readyCount > 0 && (
            <Link to="/documents/ask" className="inline-flex items-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-white/5">
              <Library size={16} /> Ask across all documents
            </Link>
          )}
          <button onClick={() => setUploadOpen((o) => !o)} aria-expanded={showUpload}
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium shadow-lg shadow-accent/20 transition hover:brightness-110">
            <Upload size={16} /> Upload Document
          </button>
        </div>
      </header>

      {config && !config.embedding.ready && (
        <div role="alert" className="flex items-start gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm">
          <AlertCircle size={18} className="mt-0.5 shrink-0 text-amber-300" />
          <div>
            <p className="font-medium text-amber-200">Document search is not ready</p>
            <p className="mt-0.5 text-slate-300">
              Orin needs the <code className="rounded bg-white/10 px-1">{config.embedding.model}</code> embedding model to read your documents.
              {config.embedding.hint ? ` ${config.embedding.hint}` : ""}
            </p>
            <button onClick={loadConfig} className="mt-2 flex items-center gap-1.5 text-xs text-accent2 hover:text-white"><RefreshCw size={12} /> Check again</button>
          </div>
        </div>
      )}

      {showUpload && <UploadZone maxMb={config?.max_mb ?? 25} onUploaded={onUploaded} />}

      {actionError && <p role="alert" className="rounded-lg border border-red-400/30 bg-red-400/10 px-4 py-2.5 text-sm text-red-300">{actionError}</p>}

      {docs === null && !loadError && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-busy="true" aria-label="Loading documents">
          {[0, 1, 2].map((i) => <div key={i} className="surface h-44 animate-pulse" />)}
        </div>
      )}

      {loadError && (
        <div className="surface flex flex-col items-center p-8 text-center">
          <p className="text-red-300">{loadError}</p>
          <button onClick={() => void load()} className="mt-4 flex items-center gap-2 rounded-lg border border-line px-4 py-2 text-sm hover:bg-white/5"><RefreshCw size={14} /> Try again</button>
        </div>
      )}

      {docs && docs.length === 0 && (
        <div className="surface flex flex-col items-center px-4 py-10 text-center">
          <span className="grid h-11 w-11 place-items-center rounded-xl bg-accent/10 text-accent"><FileText size={20} /></span>
          <p className="mt-4 font-medium">No documents yet</p>
          <p className="mt-1 max-w-sm text-sm text-slate-400">Upload your study materials to start learning with Orin's document-based AI tutor.</p>
        </div>
      )}

      {docs && docs.length > 0 && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <label className="relative min-w-[200px] flex-1 sm:max-w-xs">
              <Search size={14} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search documents" aria-label="Search documents"
                className={`${field} w-full pl-9 placeholder:text-slate-500`} />
            </label>
            <select value={filter} onChange={(e) => setFilter(e.target.value as Filter)} aria-label="Filter by status" className={field}>
              <option value="all">All statuses</option><option value="ready">Ready</option>
              <option value="processing">Processing</option><option value="failed">Failed</option>
            </select>
            <select value={sort} onChange={(e) => setSort(e.target.value as Sort)} aria-label="Sort documents" className={field}>
              <option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="name">Name (A-Z)</option>
            </select>
          </div>

          {shown.length === 0 ? (
            <p className="py-10 text-center text-sm text-slate-400">No documents match your search or filter.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {shown.map((d) => <DocumentCard key={d.id} doc={d} onView={onView} onRetry={onRetry} onDelete={onDelete} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
}
