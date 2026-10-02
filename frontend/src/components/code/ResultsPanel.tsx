import { AlertCircle, CheckCircle2, Clock, EyeOff, XCircle } from "lucide-react";
import { STATUS_LABEL, fmt, formatMs, type RunResult, type TestResult } from "../../lib/coding";

const PILL: Record<string, string> = {
  passed: "bg-emerald-500/15 text-emerald-300",
  failed: "bg-rose-500/15 text-rose-300",
  error: "bg-amber-500/15 text-amber-300",
  timeout: "bg-amber-500/15 text-amber-300",
};

function Line({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2 text-xs">
      <span className="w-16 shrink-0 text-slate-500">{label}</span>
      <code className="min-w-0 break-all whitespace-pre-wrap text-slate-200">{value}</code>
    </div>
  );
}

function TestRow({ t }: { t: TestResult }) {
  const Icon = t.passed ? CheckCircle2 : XCircle;
  return (
    <li className="rounded-lg border border-line bg-black/20 p-3">
      <div className="flex items-center gap-2 text-sm">
        <Icon size={16} className={t.passed ? "text-emerald-400" : "text-rose-400"} />
        <span className="font-medium">{t.hidden ? `Hidden test ${t.index}` : `Test ${t.index}`}</span>
        {t.hidden && <EyeOff size={13} className="text-slate-500" aria-label="Hidden test" />}
        <span className="ml-auto text-xs text-slate-500">{formatMs(t.time_ms)}</span>
      </div>
      {t.hidden ? (
        !t.passed && <p className="mt-2 text-xs text-slate-400">{t.error ?? "Wrong answer"}. The contents of hidden tests are not shown.</p>
      ) : (
        (!t.passed || t.stdout) && (
          <div className="mt-2 space-y-1">
            {t.input && <Line label="Input" value={t.input.map(fmt).join(", ")} />}
            {!t.passed && <Line label="Expected" value={fmt(t.expected)} />}
            {t.actual !== null && !t.passed && <Line label="Yours" value={t.actual} />}
            {t.error && <p className="text-xs text-amber-300">{t.error}</p>}
            {t.stdout && <Line label="Printed" value={t.stdout.replace(/\n$/, "")} />}
          </div>
        )
      )}
    </li>
  );
}

export function ResultsPanel({ result, kind }: { result: RunResult; kind: "run" | "submit" }) {
  const solved = kind === "submit" && result.status === "passed";
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${PILL[result.status]}`}>{STATUS_LABEL[result.status]}</span>
        <span className="text-sm text-slate-300">{result.passed} / {result.total} {kind === "run" ? "sample tests" : "tests"} passed</span>
        {result.results.length > 0 && (
          <span className="ml-auto flex items-center gap-1 text-xs text-slate-500">
            <Clock size={12} /> {formatMs(result.results.reduce((s, r) => s + r.time_ms, 0))}
          </span>
        )}
      </div>

      {solved && (
        <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          Solved. Every test, including the hidden ones, passed.
        </p>
      )}
      {kind === "run" && result.status === "passed" && (
        <p className="rounded-lg border border-line bg-white/5 px-3 py-2 text-sm text-slate-300">
          Sample tests pass. Press Submit to check the hidden tests too.
        </p>
      )}
      {result.error && (
        <p className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          <AlertCircle size={16} className="mt-0.5 shrink-0" /> <span className="min-w-0 break-words">{result.error}</span>
        </p>
      )}
      <ul className="space-y-2">{result.results.map((t) => <TestRow key={t.test_id} t={t} />)}</ul>
    </div>
  );
}
