import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Editor, {
  type BeforeMount,
  type OnMount,
} from "@monaco-editor/react";
import {
  AlertCircle,
  ArrowLeft,
  History,
  Play,
  RotateCcw,
  Send,
} from "lucide-react";

import { DifficultyBadge } from "../components/code/DifficultyBadge";
import { ResultsPanel } from "../components/code/ResultsPanel";
import MarkdownMessage from "../components/MarkdownMessage";
import { timeAgo } from "../lib/activity";

import {
  MAX_CODE_CHARS,
  STATUS_LABEL,
  clearDraft,
  getProblem,
  listSubmissions,
  loadDraft,
  runCode,
  saveDraft,
  submitCode,
  type Problem,
  type RunResult,
  type SubmissionItem,
  type SubmitResult,
} from "../lib/coding";

type Kind = "run" | "submit";

const btn =
  "inline-flex h-9 items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";

const LANGUAGE_LABELS: Record<string, string> = {
  python: "Python",
  javascript: "JavaScript",
  js: "JavaScript",
  java: "Java",
  c: "C",
  cpp: "C++",
  sql: "SQL",
  html: "HTML",
  css: "CSS",
  typescript: "TypeScript",
  ts: "TypeScript",
};

const MONACO_LANGUAGES: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  js: "javascript",
  java: "java",
  c: "c",
  cpp: "cpp",
  sql: "sql",
  html: "html",
  css: "css",
  typescript: "typescript",
  ts: "typescript",
};

const defineTheme: BeforeMount = (monaco) => {
  monaco.editor.defineTheme("orin", {
    base: "vs-dark",
    inherit: true,
    rules: [],
    colors: {
      "editor.background": "#0d1221",
    },
  });
};

function getLanguageLabel(language: string): string {
  const normalized = language.trim().toLowerCase();
  return LANGUAGE_LABELS[normalized] ?? language;
}

function getMonacoLanguage(language: string): string {
  const normalized = language.trim().toLowerCase();
  return MONACO_LANGUAGES[normalized] ?? normalized;
}

export default function CodeProblem() {
  const id = Number(useParams().id);

  const [problem, setProblem] = useState<Problem | null>(null);
  const [loadError, setLoadError] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState<Kind | null>(null);

  const [outcome, setOutcome] = useState<{
    kind: Kind;
    result: RunResult | SubmitResult;
  } | null>(null);

  const [actionError, setActionError] = useState("");
  const [history, setHistory] = useState<SubmissionItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  const latest = useRef(0);

  useEffect(() => {
    let cancelled = false;

    setProblem(null);
    setLoadError("");
    setOutcome(null);
    setActionError("");
    setHistory([]);
    setShowHistory(false);

    if (!Number.isInteger(id)) {
      setLoadError("Problem not found.");
      return;
    }

    getProblem(id)
      .then((p) => {
        if (!cancelled) {
          setProblem(p);
          setCode(loadDraft(id) || p.starter_code);
        }
      })
      .catch((e: Error) => {
        if (!cancelled) {
          setLoadError(e.message);
        }
      });

    listSubmissions(id)
      .then((h) => {
        if (!cancelled) {
          setHistory(h);
        }
      })
      .catch(() => {
        // History is optional.
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  const onChange = (value: string | undefined) => {
    const next = value ?? "";
    setCode(next);
    saveDraft(id, next);
  };

  const act = useCallback(
    async (kind: Kind) => {
      if (!problem || busy) {
        return;
      }

      if (!code.trim()) {
        setActionError("Write some code first.");
        return;
      }

      if (code.length > MAX_CODE_CHARS) {
        setActionError(
          `Your code is too long (limit ${MAX_CODE_CHARS.toLocaleString()} characters).`,
        );
        return;
      }

      const ticket = ++latest.current;

      setBusy(kind);
      setActionError("");

      try {
        const result =
          kind === "run"
            ? await runCode(problem.id, code, problem.language)
            : await submitCode(
                problem.id,
                code,
                problem.language,
              );

        if (ticket !== latest.current) {
          return;
        }

        setOutcome({
          kind,
          result,
        });

        if (kind === "submit") {
          listSubmissions(problem.id)
            .then(setHistory)
            .catch(() => {
              // Keep the existing history if refresh fails.
            });
        }
      } catch (e) {
        if (ticket === latest.current) {
          setActionError((e as Error).message);
        }
      } finally {
        if (ticket === latest.current) {
          setBusy(null);
        }
      }
    },
    [problem, busy, code],
  );

  const actRef = useRef(act);
  actRef.current = act;

  const onMount: OnMount = (editor, monaco) => {
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
      () => {
        void actRef.current("run");
      },
    );
  };

  const reset = () => {
    if (!problem) {
      return;
    }

    if (
      code !== problem.starter_code &&
      !window.confirm(
        "Reset to the starter code? Your current code will be lost.",
      )
    ) {
      return;
    }

    clearDraft(problem.id);
    setCode(problem.starter_code);
  };

  if (loadError) {
    return (
      <div className="mx-auto max-w-xl space-y-4 p-6 pt-16 text-center">
        <p role="alert" className="text-slate-300">
          {loadError}
        </p>

        <Link
          to="/code"
          className="inline-block rounded-lg border border-line px-4 py-2 text-sm hover:bg-white/5"
        >
          Back to problems
        </Link>
      </div>
    );
  }

  if (!problem) {
    return (
      <p className="p-6 text-sm text-slate-500">
        Loading problem…
      </p>
    );
  }

  const languageLabel = getLanguageLabel(problem.language);
  const monacoLanguage = getMonacoLanguage(problem.language);

  return (
    <div className="space-y-4 p-4 md:p-6">
      <Link
        to="/code"
        className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white"
      >
        <ArrowLeft size={14} />
        All problems
      </Link>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
        {/* Problem statement */}
        <section className="surface space-y-4 p-5">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold">
                {problem.title}
              </h1>

              <DifficultyBadge level={problem.difficulty} />

              <span className="rounded-md border border-line bg-white/5 px-2 py-1 text-xs text-slate-300">
                {languageLabel}
              </span>
            </div>

            <p className="mt-1 text-xs text-slate-500">
              {problem.topic} · {languageLabel} · define{" "}
              <code className="rounded bg-white/10 px-1">
                {problem.entry_function}
              </code>
            </p>
          </div>

          <div className="text-[15px] leading-relaxed text-slate-200">
            <MarkdownMessage text={problem.description} />
          </div>

          {problem.examples.map((ex, i) => (
            <div
              key={i}
              className="rounded-lg border border-line bg-black/20 p-3 text-sm"
            >
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                Example {i + 1}
              </p>

              {ex.input && (
                <p>
                  <span className="text-slate-500">
                    Input:{" "}
                  </span>
                  <code>{ex.input}</code>
                </p>
              )}

              {ex.output && (
                <p>
                  <span className="text-slate-500">
                    Output:{" "}
                  </span>
                  <code>{ex.output}</code>
                </p>
              )}

              {ex.explanation && (
                <p className="mt-1 text-slate-400">
                  {ex.explanation}
                </p>
              )}
            </div>
          ))}

          {problem.constraints && (
            <div>
              <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                Constraints
              </p>

              <p className="text-sm text-slate-300">
                {problem.constraints}
              </p>
            </div>
          )}

          {problem.expected_complexity && (
            <p className="text-xs text-slate-500">
              Target time complexity:{" "}
              <code>{problem.expected_complexity}</code>
            </p>
          )}

          <p className="text-xs text-slate-500">
            Run checks {problem.visible_tests} sample test
            {problem.visible_tests === 1 ? "" : "s"}.

            {problem.hidden_tests > 0 &&
              ` Submit also checks ${problem.hidden_tests} hidden test${
                problem.hidden_tests === 1 ? "" : "s"
              }.`}
          </p>
        </section>

        {/* Editor + results */}
        <section className="min-w-0 space-y-3">
          <div className="surface overflow-hidden">
            <Editor
              height="420px"
              language={monacoLanguage}
              theme="orin"
              value={code}
              onChange={onChange}
              beforeMount={defineTheme}
              onMount={onMount}
              loading={
                <span className="text-sm text-slate-500">
                  Loading editor…
                </span>
              }
              options={{
                minimap: {
                  enabled: false,
                },
                fontSize: 14,
                tabSize: 4,
                insertSpaces: true,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                padding: {
                  top: 12,
                },
                wordWrap: "on",
              }}
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => void act("run")}
              disabled={!!busy}
              title="Ctrl/Cmd + Enter"
              className={`${btn} border border-line hover:bg-white/5`}
            >
              <Play size={15} />

              {busy === "run" ? "Running…" : "Run"}
            </button>

            <button
              type="button"
              onClick={() => void act("submit")}
              disabled={!!busy}
              className={`${btn} bg-accent text-white hover:bg-accent/85`}
            >
              <Send size={15} />

              {busy === "submit"
                ? "Submitting…"
                : "Submit"}
            </button>

            <button
              type="button"
              onClick={reset}
              disabled={!!busy}
              className={`${btn} text-slate-400 hover:bg-white/5 hover:text-white`}
            >
              <RotateCcw size={15} />
              Reset
            </button>

            <button
              type="button"
              onClick={() =>
                setShowHistory((s) => !s)
              }
              aria-expanded={showHistory}
              className={`${btn} ml-auto text-slate-400 hover:bg-white/5 hover:text-white`}
            >
              <History size={15} />
              Attempts ({history.length})
            </button>
          </div>

          {actionError && (
            <p
              role="alert"
              className="flex items-start gap-2 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-200"
            >
              <AlertCircle
                size={16}
                className="mt-0.5 shrink-0"
              />

              {actionError}
            </p>
          )}

          {showHistory && (
            <div className="surface p-3">
              {history.length === 0 ? (
                <p className="text-sm text-slate-500">
                  No submissions yet.
                </p>
              ) : (
                <ul className="divide-y divide-line">
                  {history.map((s) => (
                    <li
                      key={s.id}
                      className="flex items-center gap-3 py-2 text-sm"
                    >
                      <span
                        className={
                          s.status === "passed"
                            ? "text-emerald-300"
                            : "text-slate-300"
                        }
                      >
                        {STATUS_LABEL[s.status]}
                      </span>

                      <span className="text-xs text-slate-500">
                        {s.passed}/{s.total} ·{" "}
                        {timeAgo(s.created_at)}
                      </span>

                      <button
                        type="button"
                        onClick={() => {
                          setCode(s.code);
                          saveDraft(id, s.code);
                        }}
                        className="ml-auto text-xs text-accent2 hover:text-white"
                      >
                        Load this code
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="surface p-4">
            {outcome ? (
              <ResultsPanel
                result={outcome.result}
                kind={outcome.kind}
              />
            ) : (
              <p className="text-sm text-slate-500">
                Results appear here. Press Run (Ctrl/Cmd +
                Enter) to try your code on the sample tests.
              </p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}