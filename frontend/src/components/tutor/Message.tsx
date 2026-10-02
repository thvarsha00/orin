import { useState, type ReactNode } from "react";
import { Check, Copy, Sparkles } from "lucide-react";
import MarkdownMessage from "../MarkdownMessage";
import type { ChatMessage } from "../../types";
import { ChatImage } from "./ChatImage";

export function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-2" role="status" aria-label="Orin is typing">
      {[0, 150, 300].map((d) => (
        <span key={d} className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${d}ms` }} />
      ))}
    </span>
  );
}

export function UserMessage({ message, onImageLoad }: { message: ChatMessage; onImageLoad?: () => void }) {
  const hasImage = Boolean(message.imageUrl || message.has_image);
  return (
    <div className="flex justify-end">
      <div className="flex max-w-[85%] flex-col items-end gap-1.5 md:max-w-[70%]">
        {hasImage && <ChatImage src={message.imageUrl} messageId={message.id} onLoad={onImageLoad} />}
        {message.content && (
          <div className="whitespace-pre-wrap break-words rounded-2xl bg-accent/15 px-4 py-2.5 text-[15px] leading-relaxed text-slate-100">
            {message.content}
          </div>
        )}
      </div>
    </div>
  );
}

export function AssistantMessage({ message, streaming, footer }: { message: ChatMessage; streaming: boolean; footer?: ReactNode }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(message.content); setCopied(true); setTimeout(() => setCopied(false), 1500); }
    catch { /* clipboard blocked by the browser */ }
  };
  return (
    <div className="group flex gap-3">
      <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-accent/15 text-accent"><Sparkles size={14} /></span>
      <div className="min-w-0 flex-1">
        <div className="break-words text-[15px] leading-7 text-slate-200 md:text-base md:leading-7">
          {message.content ? <MarkdownMessage text={message.content} /> : <TypingDots />}
        </div>
        {message.content && !streaming && (
          <div className="mt-1 flex opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100">
            <button onClick={copy} aria-label="Copy answer"
              className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-slate-500 hover:bg-white/5 hover:text-slate-200">
              {copied ? <><Check size={13} /> Copied</> : <><Copy size={13} /> Copy</>}
            </button>
          </div>
        )}
        {footer}
      </div>
    </div>
  );
}
