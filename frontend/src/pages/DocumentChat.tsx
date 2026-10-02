import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowDown, ArrowLeft, ArrowUp, FileText, Library, Square } from "lucide-react";
import { SourceList } from "../components/documents/SourceList";
import { LanguageSelect } from "../components/LanguageSelect";
import { ScriptSelect } from "../components/ScriptSelect";
import { AssistantMessage, UserMessage } from "../components/tutor/Message";
import { useAuth } from "../context/AuthContext";
import { api, streamDocumentChat } from "../services/api";
import type { ChatMessage, DocumentItem, Language, ScriptPref } from "../types";

const SUGGESTIONS = [
  "What are the main ideas in this material?",
  "Explain the key terms with a simple example.",
  "Give me a short quiz on this material.",
];

export default function DocumentChat() {
  const { id } = useParams();
  const documentId = id ? Number(id) : null;
  const { user } = useAuth();
  const [lang, setLang] = useState<Language>(user?.profile.preferred_language ?? "en");
  const [script, setScript] = useState<ScriptPref>(user?.profile.preferred_script ?? "auto");
  const level = user?.profile.skill_level ?? "beginner";

  const [docs, setDocs] = useState<DocumentItem[] | null>(null);
  const [loadError, setLoadError] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");
  const [showJump, setShowJump] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const stick = useRef(true);

  useEffect(() => {
    setDocs(null); setLoadError(""); setMessages([]); setError("");
    const req = documentId === null
      ? api<DocumentItem[]>("/documents").then((l) => l.filter((d) => d.status === "ready"))
      : api<DocumentItem>(`/documents/${documentId}`).then((d) => [d]);
    req.then(setDocs).catch((e: Error) => setLoadError(e.message));
    return () => abortRef.current?.abort();
  }, [documentId]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el && stick.current) el.scrollTop = el.scrollHeight;
  }, [messages]);
  useEffect(() => {   // grow the textarea with its content
    const ta = taRef.current;
    if (ta) { ta.style.height = "auto"; ta.style.height = `${Math.min(ta.scrollHeight, 176)}px`; }
  }, [input]);

  const onScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    const near = el.scrollHeight - el.scrollTop - el.clientHeight < 120;
    stick.current = near;
    setShowJump((prev) => (prev === !near ? prev : !near));
  };
  const jump = () => { const el = scrollRef.current; if (el) { stick.current = true; el.scrollTo({ top: el.scrollHeight, behavior: "smooth" }); } };

  const send = useCallback(async (override?: string) => {
    const question = (override ?? input).trim();
    if (!question || streaming || !docs) return;
    const history = messages.filter((m) => m.content.trim()).slice(-6).map((m) => ({ role: m.role, content: m.content }));
    setInput(""); setError(""); setStreaming(true); stick.current = true;
    setMessages((m) => [...m, { role: "user", content: question }, { role: "assistant", content: "" }]);
    const patchLast = (fn: (m: ChatMessage) => ChatMessage) =>
      setMessages((list) => { const c = [...list]; c[c.length - 1] = fn(c[c.length - 1]); return c; });
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    let received = false;
    try {
      const body = { question, history, language: lang, level, script,
        ...(documentId === null ? { document_ids: docs.map((d) => d.id) } : {}) };
      await streamDocumentChat(documentId, body, (e) => {
        if (e.type === "sources") patchLast((m) => ({ ...m, sources: e.sources }));
        else if (e.type === "token") { received = true; patchLast((m) => ({ ...m, content: m.content + e.text })); }
        else if (e.type === "error") setError(e.message);
      }, ctrl.signal);
    } catch (e) {
      if ((e as Error).name !== "AbortError") setError((e as Error).message);
      if (!received) { setMessages((m) => m.slice(0, -2)); setInput(question); }   // nothing arrived: undo the optimistic bubbles
    } finally {
      setStreaming(false);
      abortRef.current = null;
      taRef.current?.focus();
    }
  }, [input, streaming, docs, messages, lang, level, script, documentId]);

  const single = documentId !== null ? docs?.[0] : undefined;
  const title = documentId === null ? "All documents" : single?.filename ?? "";
  const notReady = single && single.status !== "ready";
  const empty = documentId === null && docs?.length === 0;
  const blocked = Boolean(loadError || notReady || empty);
  const knownIds = new Set(docs?.map((d) => d.id));

  const controls = (
    <>
      <LanguageSelect value={lang} onChange={setLang} compact />
      <ScriptSelect value={script} onChange={setScript} compact />
    </>
  );

  return (
    <div className="absolute inset-0 flex flex-col">
      <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-line px-3 md:px-5">
        <div className="flex min-w-0 items-center gap-2">
          <Link to="/documents" aria-label="Back to documents" className="rounded-lg p-2 text-slate-400 hover:bg-white/5 hover:text-white"><ArrowLeft size={18} /></Link>
          {documentId === null ? <Library size={18} className="shrink-0 text-accent" /> : <FileText size={18} className="shrink-0 text-accent" />}
          <h1 className="min-w-0 truncate text-sm font-medium">{title || "Documents"}</h1>
          {documentId === null && docs && <span className="hidden shrink-0 text-sm text-slate-500 sm:block">/ {docs.length} {docs.length === 1 ? "document" : "documents"}</span>}
        </div>
        <div className="flex items-center gap-2">{controls}</div>
      </header>

      <div className="relative min-h-0 flex-1">
        <div ref={scrollRef} onScroll={onScroll} className="scroll-thin h-full overflow-y-auto">
          {docs === null && !loadError && <p className="p-8 text-center text-slate-500">Loading…</p>}

          {blocked && (
            <div className="mx-auto max-w-md px-4 py-16 text-center">
              <p className="font-medium">{loadError ? "Couldn't open this document" : empty ? "No documents are ready yet" : "This document isn't ready yet"}</p>
              <p className="mt-2 text-sm text-slate-400">
                {loadError || (empty ? "Upload a document and wait until it shows Ready." : single?.status === "failed" ? "Processing failed. Retry it from the Documents page." : "It is still being processed. Try again in a moment.")}
              </p>
              <Link to="/documents" className="mt-5 inline-block rounded-lg border border-line px-4 py-2 text-sm hover:bg-white/5">Back to Documents</Link>
            </div>
          )}

          {docs && !blocked && messages.length === 0 && (
            <div className="mx-auto flex min-h-full max-w-2xl flex-col items-center justify-center px-4 py-10 text-center">
              <span className="grid h-12 w-12 place-items-center rounded-2xl bg-accent/15 text-accent">{documentId === null ? <Library size={24} /> : <FileText size={24} />}</span>
              <h2 className="mt-5 text-2xl font-semibold tracking-tight">{documentId === null ? "Ask across all your documents" : "Ask questions about this document"}</h2>
              <p className="mt-2 max-w-md text-slate-400">Orin answers from your own materials and shows where each answer came from.</p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => { setInput(s); taRef.current?.focus(); }}
                    className="rounded-xl border border-line bg-white/[0.03] px-3.5 py-2 text-sm text-slate-300 transition-colors hover:border-accent/40 hover:bg-accent/10 hover:text-white">{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.length > 0 && (
            <div className="mx-auto max-w-3xl space-y-6 px-4 py-6">
              {messages.map((m, i) => m.role === "user"
                ? <UserMessage key={i} message={m} />
                : <AssistantMessage key={i} message={m} streaming={streaming && i === messages.length - 1}
                    footer={m.sources ? <SourceList sources={m.sources} exists={(d) => knownIds.has(d)} /> : undefined} />)}
            </div>
          )}
        </div>
        {showJump && (
          <button onClick={jump} aria-label="Jump to latest" className="absolute bottom-3 left-1/2 z-10 grid h-9 w-9 -translate-x-1/2 place-items-center rounded-full border border-line bg-panel shadow-lg hover:bg-white/10"><ArrowDown size={16} /></button>
        )}
      </div>

      <footer className="shrink-0 px-3 pb-4 pt-2 md:px-5">
        <div className="mx-auto max-w-3xl">
          {error && <p role="alert" className="mb-2 rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-300">{error}</p>}
          <div className="flex items-end gap-2 rounded-2xl border border-line bg-[#0f1526] p-2 shadow-lg shadow-black/30 transition-colors focus-within:border-accent/60">
            <textarea ref={taRef} value={input} rows={1} disabled={blocked || docs === null} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }}
              placeholder={documentId === null ? "Ask a question about your documents..." : "Ask a question about this document..."} aria-label="Question"
              className="scroll-thin max-h-44 min-h-[36px] flex-1 resize-none bg-transparent px-2.5 py-1.5 text-[15px] outline-none placeholder:text-slate-500 disabled:opacity-50" />
            {streaming ? (
              <button onClick={() => abortRef.current?.abort()} aria-label="Stop generating" title="Stop generating"
                className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/10 text-white transition hover:bg-white/20"><Square size={14} fill="currentColor" /></button>
            ) : (
              <button onClick={() => void send()} disabled={!input.trim() || blocked || docs === null} aria-label="Send question"
                className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-accent text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"><ArrowUp size={18} /></button>
            )}
          </div>
          <p className="mt-2 text-center text-xs text-slate-600">Answers come from your uploaded materials. Enter to send, Shift+Enter for a new line.</p>
        </div>
      </footer>
    </div>
  );
}
