import type { Conversation } from "../types";

/** The backend sends naive UTC timestamps; make sure the browser reads them as UTC. */
export function parseUtc(s: string): Date {
  return new Date(/(Z|[+-]\d\d:?\d\d)$/.test(s) ? s : `${s}Z`);
}

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

/** Consecutive days (ending today, or yesterday) on which the user started a tutor session. */
export function sessionStreak(convs: Conversation[]): number {
  const days = new Set(convs.map((c) => dayKey(parseUtc(c.created_at))));
  const cursor = new Date();
  if (!days.has(dayKey(cursor))) cursor.setDate(cursor.getDate() - 1);
  let streak = 0;
  while (days.has(dayKey(cursor))) { streak += 1; cursor.setDate(cursor.getDate() - 1); }
  return streak;
}

export function sessionsInLastDays(convs: Conversation[], days: number): number {
  const since = Date.now() - days * 86_400_000;
  return convs.filter((c) => parseUtc(c.created_at).getTime() >= since).length;
}

export function timeAgo(s: string): string {
  const mins = Math.max(0, Math.round((Date.now() - parseUtc(s).getTime()) / 60_000));
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} hr ago`;
  const d = Math.round(hrs / 24);
  return d === 1 ? "Yesterday" : `${d} days ago`;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "?") + (parts.length > 1 ? parts[parts.length - 1][0] : "")).toUpperCase();
}

/** Groups conversations (already newest-first) into Today / Yesterday / Previous 7 days / Older. */
export function groupConversations(convs: Conversation[]): { label: string; items: Conversation[] }[] {
  const startOfToday = new Date(); startOfToday.setHours(0, 0, 0, 0);
  const buckets: Record<string, Conversation[]> = { Today: [], Yesterday: [], "Previous 7 days": [], Older: [] };
  for (const c of convs) {
    const d = parseUtc(c.created_at); d.setHours(0, 0, 0, 0);
    const days = Math.round((startOfToday.getTime() - d.getTime()) / 86_400_000);
    buckets[days <= 0 ? "Today" : days === 1 ? "Yesterday" : days <= 7 ? "Previous 7 days" : "Older"].push(c);
  }
  return Object.entries(buckets).filter(([, items]) => items.length).map(([label, items]) => ({ label, items }));
}
