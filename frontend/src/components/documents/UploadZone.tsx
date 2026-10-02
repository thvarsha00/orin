import { useCallback, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, UploadCloud, X } from "lucide-react";
import { ACCEPT, formatSize, validateFile } from "../../lib/documents";
import { uploadDocument } from "../../services/api";
import type { DocumentItem } from "../../types";

interface Job { id: number; name: string; size: number; progress: number; state: "uploading" | "done" | "error"; error?: string }

let nextId = 1;

export function UploadZone({ maxMb, onUploaded }: { maxMb: number; onUploaded: (d: DocumentItem) => void }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const depth = useRef(0);
  const patch = (id: number, p: Partial<Job>) => setJobs((js) => js.map((j) => (j.id === id ? { ...j, ...p } : j)));

  const start = useCallback(async (files: File[]) => {
    for (const file of files) {                      // one at a time keeps server load and progress readable
      const id = nextId++;
      const problem = validateFile(file, maxMb);
      setJobs((js) => [...js, { id, name: file.name, size: file.size, progress: 0, state: problem ? "error" : "uploading", error: problem ?? undefined }]);
      if (problem) continue;
      try {
        const doc = await uploadDocument(file, (f) => patch(id, { progress: f }));
        patch(id, { progress: 1, state: "done" });
        onUploaded(doc);
        setTimeout(() => setJobs((js) => js.filter((j) => j.id !== id)), 4000);
      } catch (e) {
        patch(id, { state: "error", error: (e as Error).message });
      }
    }
  }, [maxMb, onUploaded]);

  const pick = (list: FileList | null) => { if (list?.length) void start(Array.from(list)); if (inputRef.current) inputRef.current.value = ""; };

  return (
    <section aria-label="Upload documents" className="space-y-3">
      <div
        onDragEnter={(e) => { e.preventDefault(); depth.current++; setDragging(true); }}
        onDragLeave={() => { if (--depth.current <= 0) { depth.current = 0; setDragging(false); } }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); depth.current = 0; setDragging(false); pick(e.dataTransfer.files); }}
        className={`surface flex flex-col items-center border-dashed px-6 py-8 text-center transition-colors ${dragging ? "!border-accent bg-accent/10" : ""}`}
      >
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-accent/10 text-accent"><UploadCloud size={22} /></span>
        <p className="mt-3 font-medium">Drag and drop your study materials here</p>
        <p className="mt-1 text-sm text-slate-400">PDF files (and .txt / .md notes), up to {maxMb} MB each</p>
        <button type="button" onClick={() => inputRef.current?.click()}
          className="mt-4 rounded-lg border border-line px-4 py-2 text-sm font-medium transition-colors hover:border-accent/50 hover:bg-accent/10">
          Browse files
        </button>
        <input ref={inputRef} type="file" accept={ACCEPT} multiple hidden onChange={(e) => pick(e.target.files)} aria-label="Choose files to upload" />
      </div>

      {jobs.length > 0 && (
        <ul className="space-y-2" aria-live="polite">
          {jobs.map((j) => (
            <li key={j.id} className="surface px-4 py-3">
              <div className="flex items-center gap-3 text-sm">
                {j.state === "uploading" && <Loader2 size={16} className="shrink-0 animate-spin text-accent2" />}
                {j.state === "done" && <CheckCircle2 size={16} className="shrink-0 text-emerald-400" />}
                {j.state === "error" && <AlertCircle size={16} className="shrink-0 text-red-400" />}
                <span className="min-w-0 flex-1 truncate">{j.name}</span>
                <span className="shrink-0 text-xs text-slate-500">
                  {j.state === "uploading" && `Uploading ${Math.round(j.progress * 100)}%`}
                  {j.state === "done" && "Uploaded, processing"}
                  {j.state === "error" && formatSize(j.size)}
                </span>
                {j.state === "error" && (
                  <button onClick={() => setJobs((js) => js.filter((x) => x.id !== j.id))} aria-label="Dismiss"
                    className="rounded p-1 text-slate-500 hover:bg-white/5 hover:text-slate-200"><X size={14} /></button>
                )}
              </div>
              {j.state === "uploading" && (
                <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/10">
                  <div className="h-full rounded-full bg-accent transition-[width] duration-150" style={{ width: `${j.progress * 100}%` }} />
                </div>
              )}
              {j.state === "error" && <p className="mt-1.5 pl-7 text-xs text-red-300">{j.error}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
