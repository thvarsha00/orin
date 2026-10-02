import { useEffect, useState } from "react";
import { NavLink, Navigate, Outlet, useLocation } from "react-router-dom";
import {
  BarChart3, ChevronsLeft, ChevronsRight, Code2, FileText, GraduationCap, LayoutDashboard, LogOut, Menu,
  Settings, Sparkles, X,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { initials } from "../lib/activity";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/tutor", label: "AI Tutor", icon: GraduationCap },
  { to: "/code", label: "Orin Code", icon: Sparkles },
  { to: "/practice", label: "Practice", icon: Code2 },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/progress", label: "Progress", icon: BarChart3 },
];

const linkClass = (collapsed: boolean) => ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-lg border-l-2 py-2 text-sm transition-colors ${collapsed ? "justify-center px-0" : "px-3"} ${
    isActive ? "border-accent bg-accent/15 text-white" : "border-transparent text-slate-400 hover:bg-white/5 hover:text-slate-100"}`;

function SidebarBody({ collapsed, onToggle, onClose }: { collapsed: boolean; onToggle?: () => void; onClose?: () => void }) {
  const { user, logout } = useAuth();
  const name = user?.profile.display_name ?? "";
  const level = user?.profile.skill_level ?? "";
  return (
    <div className="flex h-full flex-col p-3">
      <div className={`mb-6 flex items-center ${collapsed ? "justify-center" : "justify-between px-2"} pt-1`}>
        {collapsed ? (
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-accent/20 text-lg font-bold text-accent">O</span>
        ) : (
          <div>
            <div className="text-xl font-bold tracking-tight">Orin</div>
            <div className="text-xs text-slate-500">Learn. Code. Evolve.</div>
          </div>
        )}
        {onClose && <button onClick={onClose} aria-label="Close menu" className="rounded-md p-1.5 text-slate-400 hover:bg-white/5"><X size={18} /></button>}
      </div>

      <nav aria-label="Main" className="flex flex-col gap-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} title={collapsed ? label : undefined} className={linkClass(collapsed)}>
            <Icon size={18} className="shrink-0" /> {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-1 border-t border-line pt-3">
        <NavLink to="/settings" title={collapsed ? "Settings" : undefined} className={linkClass(collapsed)}>
          <Settings size={18} className="shrink-0" /> {!collapsed && "Settings"}
        </NavLink>
        <div className={`flex items-center gap-3 rounded-lg py-2 ${collapsed ? "justify-center" : "px-2"}`}>
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-accent to-accent2/80 text-xs font-semibold">{initials(name)}</span>
          {!collapsed && (
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{name}</p>
              <p className="text-xs capitalize text-slate-500">{level} learner</p>
            </div>
          )}
        </div>
        <button onClick={logout} title={collapsed ? "Log out" : undefined}
          className={`flex w-full items-center gap-3 rounded-lg py-2 text-sm text-slate-400 transition-colors hover:bg-red-500/10 hover:text-red-300 ${collapsed ? "justify-center" : "px-3"}`}>
          <LogOut size={18} className="shrink-0" /> {!collapsed && "Log out"}
        </button>
        {onToggle && (
          <button onClick={onToggle} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={`hidden w-full items-center gap-3 rounded-lg py-2 text-xs text-slate-500 hover:bg-white/5 hover:text-slate-300 md:flex ${collapsed ? "justify-center" : "px-3"}`}>
            {collapsed ? <ChevronsRight size={16} /> : <><ChevronsLeft size={16} /> Collapse</>}
          </button>
        )}
      </div>
    </div>
  );
}

export function AppLayout() {
  const { user, loading } = useAuth();
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState(() => {
    try { return localStorage.getItem("orin_sidebar_collapsed") === "1"; } catch { return false; }
  });
  const [drawer, setDrawer] = useState(false);

  useEffect(() => { setDrawer(false); }, [pathname]);
  useEffect(() => {
    if (!drawer) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setDrawer(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawer]);

  const toggle = () => setCollapsed((c) => {
    try { localStorage.setItem("orin_sidebar_collapsed", c ? "0" : "1"); } catch { /* storage unavailable */ }
    return !c;
  });

  if (loading) return <div className="grid h-screen place-items-center text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="flex h-screen flex-col md:flex-row">
      {/* Desktop / tablet sidebar */}
      <aside className={`hidden shrink-0 border-r border-line bg-sidebar transition-[width] duration-200 md:block ${collapsed ? "w-[72px]" : "w-60"}`}>
        <SidebarBody collapsed={collapsed} onToggle={toggle} />
      </aside>

      {/* Mobile top bar */}
      <div className="flex shrink-0 items-center gap-3 border-b border-line bg-sidebar px-4 py-3 md:hidden">
        <button onClick={() => setDrawer(true)} aria-label="Open menu" className="rounded-md p-1.5 text-slate-300 hover:bg-white/5"><Menu size={20} /></button>
        <span className="font-bold tracking-tight">Orin</span>
      </div>

      {/* Mobile drawer */}
      {drawer && (
        <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <div className="absolute inset-0 bg-black/60" onClick={() => setDrawer(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-line bg-sidebar shadow-2xl">
            <SidebarBody collapsed={false} onClose={() => setDrawer(false)} />
          </aside>
        </div>
      )}

      <main className="relative min-h-0 min-w-0 flex-1 overflow-y-auto"><Outlet /></main>
    </div>
  );
}
