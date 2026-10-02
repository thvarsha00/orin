import {
  ArrowRight,
  CheckCircle2,
  Code2,
  Loader2,
  Target,
  Trophy,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getCodingProgress,
  type CodingProgress,
} from "../lib/coding";

function formatDate(value: string): string {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function statusLabel(status: string): string {
  switch (status) {
    case "passed":
      return "Passed";
    case "failed":
      return "Failed";
    case "timeout":
      return "Timed out";
    case "error":
      return "Error";
    default:
      return status;
  }
}

function statusClass(status: string): string {
  switch (status) {
    case "passed":
      return "text-emerald-400";
    case "failed":
      return "text-amber-400";
    case "timeout":
      return "text-orange-400";
    case "error":
      return "text-red-400";
    default:
      return "text-slate-400";
  }
}

export default function Progress() {
  const [progress, setProgress] =
    useState<CodingProgress | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProgress() {
      try {
        setLoading(true);
        setError(null);

        const data = await getCodingProgress();

        if (!cancelled) {
          setProgress(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load your coding progress.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadProgress();

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="mx-auto flex min-h-[60vh] max-w-7xl items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-slate-400">
          <Loader2
            size={18}
            className="animate-spin text-accent"
          />
          Loading your progress...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-7xl pb-12">
        <section className="rounded-2xl border border-red-400/20 bg-panel px-6 py-8 sm:px-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-red-400">
            Progress unavailable
          </p>

          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
            We could not load your progress
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Your coding progress is calculated from your saved
            submissions. Please make sure you are signed in and the
            backend is running, then try again.
          </p>

          <p className="mt-4 rounded-lg border border-line bg-slate-950/40 p-3 text-xs text-slate-500">
            {error}
          </p>

          <Link
            to="/code"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            Go to Orin Code
            <ArrowRight size={16} />
          </Link>
        </section>
      </div>
    );
  }

  if (!progress) {
    return null;
  }

  const hasActivity =
    progress.total_submissions > 0;

  const solvedProgress =
    progress.problems_attempted > 0
      ? Math.round(
          (progress.problems_solved /
            progress.problems_attempted) *
            100,
        )
      : 0;

  return (
    <div className="mx-auto max-w-7xl space-y-8 pb-12">
      <section className="relative overflow-hidden rounded-2xl border border-line bg-panel px-6 py-8 sm:px-8">
        <div className="absolute -right-24 -top-24 h-64 w-64 rounded-full bg-accent/10 blur-3xl" />

        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent2">
            Your learning journey
          </p>

          <div className="mt-3 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Progress
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
                Your coding progress is based on real submissions
                and test results recorded by Orin.
              </p>
            </div>

            <Link
              to="/code"
              className="inline-flex w-fit items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
            >
              Continue coding
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {!hasActivity ? (
        <section className="rounded-xl border border-line bg-panel p-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <Code2 size={22} />
          </div>

          <h2 className="mt-5 text-xl font-semibold text-white">
            Your coding journey starts here
          </h2>

          <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-400">
            You have not submitted a coding solution yet. Once
            you start solving problems, Orin will show your real
            attempts, solved problems, test accuracy, language
            usage, and recent activity here.
          </p>

          <Link
            to="/code"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90"
          >
            Start coding
            <ArrowRight size={16} />
          </Link>
        </section>
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl border border-line bg-panel p-5">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-accent/10 p-2 text-accent">
                  <Code2 size={18} />
                </div>

                <span className="text-xs text-slate-500">
                  Attempts
                </span>
              </div>

              <p className="mt-5 text-3xl font-semibold text-white">
                {progress.total_submissions}
              </p>

              <p className="mt-1 text-sm text-slate-400">
                Total submissions
              </p>
            </div>

            <div className="rounded-xl border border-line bg-panel p-5">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-emerald-400/10 p-2 text-emerald-300">
                  <CheckCircle2 size={18} />
                </div>

                <span className="text-xs text-slate-500">
                  Solved
                </span>
              </div>

              <p className="mt-5 text-3xl font-semibold text-white">
                {progress.problems_solved}
              </p>

              <p className="mt-1 text-sm text-slate-400">
                Problems solved
              </p>
            </div>

            <div className="rounded-xl border border-line bg-panel p-5">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-violet-400/10 p-2 text-violet-300">
                  <Target size={18} />
                </div>

                <span className="text-xs text-slate-500">
                  Coverage
                </span>
              </div>

              <p className="mt-5 text-3xl font-semibold text-white">
                {progress.problems_attempted}
              </p>

              <p className="mt-1 text-sm text-slate-400">
                Problems attempted
              </p>
            </div>

            <div className="rounded-xl border border-line bg-panel p-5">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-sky-400/10 p-2 text-sky-300">
                  <Trophy size={18} />
                </div>

                <span className="text-xs text-slate-500">
                  Tests
                </span>
              </div>

              <p className="mt-5 text-3xl font-semibold text-white">
                {progress.test_accuracy}%
              </p>

              <p className="mt-1 text-sm text-slate-400">
                Test accuracy
              </p>
            </div>
          </section>

          <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
            <section className="rounded-xl border border-line bg-panel p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-accent2">
                    Coding activity
                  </p>

                  <h2 className="mt-2 text-xl font-semibold text-white">
                    What your submissions show
                  </h2>
                </div>

                <Code2
                  className="text-slate-500"
                  size={22}
                />
              </div>

              <div className="mt-7 space-y-6">
                <div>
                  <div className="mb-2 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        Problems solved
                      </p>

                      <p className="mt-0.5 text-xs text-slate-500">
                        {progress.problems_solved} of{" "}
                        {progress.problems_attempted} attempted
                      </p>
                    </div>

                    <span className="text-sm font-semibold text-slate-300">
                      {solvedProgress}%
                    </span>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-accent transition-all"
                      style={{
                        width: `${solvedProgress}%`,
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        Tests passed
                      </p>

                      <p className="mt-0.5 text-xs text-slate-500">
                        {progress.tests_passed} of{" "}
                        {progress.tests_total} tests
                      </p>
                    </div>

                    <span className="text-sm font-semibold text-slate-300">
                      {progress.test_accuracy}%
                    </span>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-800">
                    <div
                      className="h-full rounded-full bg-accent transition-all"
                      style={{
                        width: `${progress.test_accuracy}%`,
                      }}
                    />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-line bg-slate-950/30 p-4">
                    <p className="text-xs text-slate-500">
                      Python submissions
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-white">
                      {progress.python_submissions}
                    </p>
                  </div>

                  <div className="rounded-xl border border-line bg-slate-950/30 p-4">
                    <p className="text-xs text-slate-500">
                      JavaScript submissions
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-white">
                      {progress.javascript_submissions}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-line bg-panel p-6">
              <p className="text-xs font-semibold uppercase tracking-widest text-accent2">
                Current data
              </p>

              <div className="mt-4 rounded-xl border border-line bg-slate-950/40 p-5">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-accent/10 p-2 text-accent">
                    <Target size={18} />
                  </div>

                  <div>
                    <p className="text-sm font-semibold text-white">
                      Submission-based progress
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Updated from your coding activity
                    </p>
                  </div>
                </div>

                <p className="mt-4 text-sm leading-6 text-slate-400">
                  Orin currently tracks your coding attempts,
                  solved problems, test results, and language
                  activity. Skill mastery, XP, levels, and learning
                  streaks are not being fabricated from incomplete
                  data.
                </p>

                <Link
                  to="/code"
                  className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-accent2 hover:underline"
                >
                  Practice more problems
                  <ArrowRight size={15} />
                </Link>
              </div>
            </section>
          </div>

          <section className="rounded-xl border border-line bg-panel p-6">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-accent/10 p-2 text-accent">
                <Code2 size={18} />
              </div>

              <div>
                <p className="text-xs font-semibold uppercase tracking-widest text-accent2">
                  Recent activity
                </p>

                <h2 className="mt-1 text-xl font-semibold text-white">
                  Your latest submissions
                </h2>
              </div>
            </div>

            <div className="mt-7 overflow-hidden rounded-xl border border-line">
              <div className="divide-y divide-line">
                {progress.recent_submissions.map(
                  (submission, index) => (
                    <div
                      key={`${submission.problem_id}-${submission.created_at}-${index}`}
                      className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="flex items-center gap-3">
                        {submission.status === "passed" ? (
                          <CheckCircle2
                            size={18}
                            className="shrink-0 text-emerald-400"
                          />
                        ) : (
                          <XCircle
                            size={18}
                            className={`shrink-0 ${statusClass(
                              submission.status,
                            )}`}
                          />
                        )}

                        <div>
                          <p className="text-sm font-medium text-slate-200">
                            Problem #{submission.problem_id}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {submission.language} ·{" "}
                            {formatDate(
                              submission.created_at,
                            )}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-sm">
                        <span
                          className={`font-medium ${statusClass(
                            submission.status,
                          )}`}
                        >
                          {statusLabel(
                            submission.status,
                          )}
                        </span>

                        <span className="text-slate-500">
                          {submission.passed}/
                          {submission.total} tests
                        </span>
                      </div>
                    </div>
                  ),
                )}
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}