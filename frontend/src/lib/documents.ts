import type { DocStatus, DocumentItem } from "../types";

export const IN_PROGRESS: DocStatus[] = ["queued", "extracting", "embedding"];
export const isBusy = (d: DocumentItem) => IN_PROGRESS.includes(d.status);

export const STATUS_LABEL: Record<DocStatus, string> = {
  queued: "Processing", extracting: "Extracting text", embedding: "Creating embeddings", ready: "Ready", failed: "Failed",
};

export const TYPE_LABEL: Record<DocumentItem["file_type"], string> = { pdf: "PDF", txt: "Text", md: "Markdown" };
export const ACCEPT = ".pdf,.txt,.md,application/pdf,text/plain,text/markdown";

export function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Client-side check for instant feedback; the server repeats it and is the authority. */
export function validateFile(file: File, maxMb: number): string | null {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!["pdf", "txt", "md"].includes(ext)) return "Unsupported file. Please choose a PDF (or a .txt / .md notes file).";
  if (file.size === 0) return "This file is empty.";
  if (file.size > maxMb * 1024 * 1024) return `That file is too large. The limit is ${maxMb} MB.`;
  return null;
}

export function formatDate(iso: string): string {
  const d = new Date(iso.endsWith("Z") ? iso : `${iso}Z`);   // server timestamps are UTC without a suffix
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}
