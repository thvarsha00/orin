export function ComingSoon({ title, phase, note }: { title: string; phase: string; note: string }) {
  return (
    <div className="mx-auto max-w-xl pt-24 text-center">
      <p className="text-xs font-medium uppercase tracking-widest text-accent2">{phase}</p>
      <h1 className="mt-2 text-2xl font-semibold">{title}</h1>
      <p className="mt-3 text-slate-400">{note}</p>
      <p className="mt-6 inline-block rounded-md border border-line px-3 py-1 text-xs text-slate-500">TODO — not implemented yet</p>
    </div>
  );
}
