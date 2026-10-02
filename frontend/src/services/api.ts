import type { DocumentItem, DocSource } from "../types";

const TOKEN_KEY = "orin_token";
export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t: string | null) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY));

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

async function failure(res: Response): Promise<ApiError> {
  let msg = "Something went wrong. Please try again.";
  try { msg = (await res.json()).error ?? msg; } catch { /* non-JSON error body */ }
  return new ApiError(msg, res.status);
}

function headers(json = true): HeadersInit {
  const h: Record<string, string> = json ? { "Content-Type": "application/json" } : {};
  const t = getToken();
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

export async function api<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, { method, headers: headers(), body: body ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError("Can't reach the Orin server. Is the backend running?", 0);
  }
  if (!res.ok) throw await failure(res);
  return res.status === 204 ? (undefined as T) : res.json();
}

async function streamPost(
  path: string, body: BodyInit, json: boolean, onChunk: (text: string) => void,
  signal?: AbortSignal, onConversationId?: (id: number) => void,
): Promise<number> {
  let res: Response;
  try {
    res = await fetch(path, { method: "POST", headers: headers(json), body, signal });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError("Can't reach the Orin server. Is the backend running?", 0);
  }
  if (!res.ok || !res.body) throw await failure(res);
  const earlyId = Number(res.headers.get("X-Conversation-Id"));
  if (earlyId && onConversationId) onConversationId(earlyId);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
  }
  return Number(res.headers.get("X-Conversation-Id"));
}

/** Streams plain-text chunks from the tutor endpoint. Returns the conversation id. */
export function streamTutor(
  body: unknown, onChunk: (text: string) => void, signal?: AbortSignal, onConversationId?: (id: number) => void,
): Promise<number> {
  return streamPost("/api/tutor/chat", JSON.stringify(body), true, onChunk, signal, onConversationId);
}

/** Same as streamTutor, but sends a multipart form that includes the attached image. */
export function streamTutorImage(
  form: FormData, onChunk: (text: string) => void, signal?: AbortSignal, onConversationId?: (id: number) => void,
): Promise<number> {
  return streamPost("/api/tutor/chat/image", form, false, onChunk, signal, onConversationId);
}

// Saved images need the login token, which <img src> cannot send, so fetch them as blobs (cached per message).
const imageCache = new Map<number, Promise<string>>();
export function fetchMessageImage(messageId: number): Promise<string> {
  let hit = imageCache.get(messageId);
  if (!hit) {
    hit = fetch(`/api/tutor/messages/${messageId}/image`, { headers: headers(false) })
      .then(async (res) => { if (!res.ok) throw await failure(res); return URL.createObjectURL(await res.blob()); })
      .catch((e) => { imageCache.delete(messageId); throw e; });
    imageCache.set(messageId, hit);
  }
  return hit;
}

// ---- Documents ---------------------------------------------------------------------------------------------

/** Uploads a document with real byte-level progress (fetch cannot report upload progress, XHR can). */
export function uploadDocument(file: File, onProgress: (fraction: number) => void, signal?: AbortSignal): Promise<DocumentItem> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/documents");
    const t = getToken();
    if (t) xhr.setRequestHeader("Authorization", `Bearer ${t}`);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable) onProgress(e.loaded / e.total); };
    xhr.onerror = () => reject(new ApiError("Can't reach the Orin server. Is the backend running?", 0));
    xhr.onabort = () => reject(new DOMException("Aborted", "AbortError"));
    xhr.onload = () => {
      let body: { error?: string } | DocumentItem | null = null;
      try { body = JSON.parse(xhr.responseText); } catch { /* non-JSON body */ }
      if (xhr.status >= 200 && xhr.status < 300 && body) return resolve(body as DocumentItem);
      reject(new ApiError((body as { error?: string } | null)?.error ?? "Upload failed. Please try again.", xhr.status));
    };
    signal?.addEventListener("abort", () => xhr.abort());
    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

export type DocChatEvent =
  | { type: "sources"; sources: DocSource[] }
  | { type: "token"; text: string }
  | { type: "error"; message: string }
  | { type: "done" };

/** Streams a grounded answer (newline-delimited JSON events) for one document, or all when `documentId` is null. */
export async function streamDocumentChat(
  documentId: number | null, body: unknown, onEvent: (e: DocChatEvent) => void, signal?: AbortSignal,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(documentId === null ? "/api/documents/chat" : `/api/documents/${documentId}/chat`,
      { method: "POST", headers: headers(), body: JSON.stringify(body), signal });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError("Can't reach the Orin server. Is the backend running?", 0);
  }
  if (!res.ok || !res.body) throw await failure(res);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const flush = (line: string) => { if (line.trim()) onEvent(JSON.parse(line) as DocChatEvent); };
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    lines.forEach(flush);
  }
  flush(buffer + decoder.decode());
}

/** Opens the original file (at a page, for PDFs) in a new tab. The file needs the login token, so it goes via a blob. */
export async function openDocument(documentId: number, page?: number | null): Promise<void> {
  const tab = window.open("", "_blank");   // opened synchronously so the popup blocker allows it
  try {
    const res = await fetch(`/api/documents/${documentId}/file`, { headers: headers(false) });
    if (!res.ok) throw await failure(res);
    const url = URL.createObjectURL(await res.blob());
    const target = page ? `${url}#page=${page}` : url;
    if (tab) tab.location.href = target; else window.location.assign(target);
    setTimeout(() => URL.revokeObjectURL(url), 5 * 60_000);
  } catch (e) {
    tab?.close();
    throw e;
  }
}
