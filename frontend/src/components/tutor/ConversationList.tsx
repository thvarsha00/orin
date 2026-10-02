import { useMemo, useState } from "react";
import { PanelLeftClose, Plus, Search, Trash2, X } from "lucide-react";
import { groupConversations } from "../../lib/activity";
import type { Conversation } from "../../types";

export function ConversationList({ convs, activeId, onOpen, onNew, onDelete, onCollapse }: {
  convs: Conversation[]; activeId: number | null;
  onOpen: (id: number) => void; onNew: () => void; onDelete: (id: number) => void; onCollapse?: () => void;
}) {
  const [query, setQuery] = useState("");
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    return groupConversations(q ? convs.filter((c) => c.title.toLowerCase().includes(q)) : convs);
  }, [convs, query]);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 pb-2 pt-4">
        <h2 className="text-sm font-medium text-slate-300">Chats</h2>
        <div className="flex items-center gap-1">
          <button onClick={onNew} aria-label="New chat"
            className="flex items-center gap-1.5 rounded-lg bg-accent/15 px-2.5 py-1.5 text-xs font-medium text-white transition-colors hover:bg-accent/25">
            <Plus size={14} /> New chat
          </button>
          {onCollapse && (
            <button onClick={onCollapse} aria-label="Hide chats" title="Hide chats"
              className="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-white/5 hover:text-slate-200"><PanelLeftClose size={16} /></button>
          )}
        </div>
      </div>

      <div className="px-3 pb-2">
        <label className="flex items-center gap-2 rounded-lg bg-white/5 px-2.5 py-1.5 text-slate-500 focus-within:ring-1 focus-within:ring-accent/50">
          <Search size={14} />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search chats" aria-label="Search chats"
            className="min-w-0 flex-1 bg-transparent text-sm text-slate-200 outline-none placeholder:text-slate-500" />
          {query && <button onClick={() => setQuery("")} aria-label="Clear search"><X size={14} /></button>}
        </label>
      </div>

      <div className="scroll-thin min-h-0 flex-1 overflow-y-auto px-2 pb-3">
        {convs.length === 0 && <p className="px-3 py-2 text-xs text-slate-500">No conversations yet.</p>}
        {convs.length > 0 && groups.length === 0 && <p className="px-3 py-2 text-xs text-slate-500">No chats match your search.</p>}
        {groups.map((g) => (
          <div key={g.label} className="mt-3 first:mt-1">
            <p className="px-3 pb-1 text-[11px] font-medium uppercase tracking-wide text-slate-500">{g.label}</p>
            {g.items.map((c) => (
              <div key={c.id} className={`group flex items-center rounded-lg transition-colors ${c.id === activeId ? "bg-accent/15" : "hover:bg-white/5"}`}>
                <button onClick={() => onOpen(c.id)} title={c.title}
                  className={`min-w-0 flex-1 truncate px-3 py-2 text-left text-sm ${c.id === activeId ? "text-white" : "text-slate-300"}`}>{c.title}</button>
                {confirmId === c.id ? (
                  <span className="flex items-center gap-1 pr-2 text-xs">
                    <button onClick={() => { setConfirmId(null); onDelete(c.id); }} className="rounded px-1.5 py-0.5 text-red-300 hover:bg-red-500/10">Delete</button>
                    <button onClick={() => setConfirmId(null)} className="rounded px-1.5 py-0.5 text-slate-400 hover:bg-white/5">Cancel</button>
                  </span>
                ) : (
                  <button onClick={() => setConfirmId(c.id)} aria-label={`Delete ${c.title}`}
                    className="px-2 text-slate-500 opacity-0 transition hover:text-red-400 focus:opacity-100 group-hover:opacity-100"><Trash2 size={14} /></button>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
