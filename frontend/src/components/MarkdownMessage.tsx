import { Children, isValidElement, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import bash from "highlight.js/lib/languages/bash";
import c from "highlight.js/lib/languages/c";
import cpp from "highlight.js/lib/languages/cpp";
import css from "highlight.js/lib/languages/css";
import java from "highlight.js/lib/languages/java";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import python from "highlight.js/lib/languages/python";
import sql from "highlight.js/lib/languages/sql";
import typescript from "highlight.js/lib/languages/typescript";
import xml from "highlight.js/lib/languages/xml";
import { Check, Copy } from "lucide-react";

const LANGS = { bash, c, cpp, css, java, javascript, js: javascript, json, python, py: python, sql, typescript, ts: typescript, xml, html: xml };

/** Plain text of a rendered React subtree (used by the code-block copy button). */
function textOf(node: ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (isValidElement(node)) return textOf((node.props as { children?: ReactNode }).children);
  return Children.toArray(node).map(textOf).join("");
}

function CodeBlock({ children }: { children?: ReactNode }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(textOf(children).replace(/\n$/, "")); setCopied(true); setTimeout(() => setCopied(false), 1500); }
    catch { /* clipboard blocked by the browser */ }
  };
  return (
    <div className="group/code relative my-4">
      <button type="button" onClick={copy} aria-label="Copy code"
        className="absolute right-2 top-2 flex items-center gap-1.5 rounded-md bg-white/5 px-2 py-1 text-xs text-slate-400 opacity-0 transition hover:bg-white/10 hover:text-white focus:opacity-100 group-hover/code:opacity-100">
        {copied ? <><Check size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
      </button>
      <pre className="scroll-thin overflow-x-auto rounded-xl border border-line bg-black/30 p-4 text-[13.5px] leading-relaxed">{children}</pre>
    </div>
  );
}

// Renders tutor replies directly on the page background: readable headings, lists, tables and code.
export default function MarkdownMessage({ text }: { text: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[[rehypeHighlight, { languages: LANGS, detect: false, ignoreMissing: true }]]}
      components={{
        h1: (p) => <h2 className="mb-2 mt-6 text-xl font-semibold text-white first:mt-0" {...p} />,
        h2: (p) => <h3 className="mb-2 mt-6 text-lg font-semibold text-white first:mt-0" {...p} />,
        h3: (p) => <h4 className="mb-1.5 mt-5 text-base font-semibold text-white first:mt-0" {...p} />,
        h4: (p) => <h5 className="mb-1.5 mt-4 text-[15px] font-semibold text-white first:mt-0" {...p} />,
        p: (p) => <p className="my-3 first:mt-0 last:mb-0" {...p} />,
        ul: (p) => <ul className="my-3 list-disc space-y-1.5 pl-6 marker:text-slate-500" {...p} />,
        ol: (p) => <ol className="my-3 list-decimal space-y-1.5 pl-6 marker:text-slate-500" {...p} />,
        strong: (p) => <strong className="font-semibold text-white" {...p} />,
        a: (p) => <a className="text-accent2 underline underline-offset-2 hover:text-white" target="_blank" rel="noreferrer" {...p} />,
        blockquote: (p) => <blockquote className="my-4 border-l-2 border-accent/50 pl-4 text-slate-400" {...p} />,
        hr: () => <div className="my-5 border-t border-line" />,
        pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
        code: ({ className, children, ...rest }) =>
          className ? (
            <code className={className} {...rest}>{children}</code>
          ) : (
            <code className="rounded-md bg-white/10 px-1.5 py-0.5 text-[0.88em] text-slate-100" {...rest}>{children}</code>
          ),
        table: (p) => <div className="scroll-thin my-4 overflow-x-auto"><table className="w-full border-collapse text-sm" {...p} /></div>,
        th: (p) => <th className="border border-line bg-white/5 px-3 py-2 text-left font-medium" {...p} />,
        td: (p) => <td className="border border-line px-3 py-2" {...p} />,
      }}
    >
      {text}
    </ReactMarkdown>
  );
}
