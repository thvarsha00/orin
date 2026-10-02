import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Code2,
  FileText,
  Flame,
  GraduationCap,
  History,
  Languages,
  MessageSquare,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { AiStatusCard } from "../components/dashboard/AiStatusCard";
import { EmptyState } from "../components/dashboard/EmptyState";
import {
  MetricCard,
  type MetricState,
} from "../components/dashboard/MetricCard";
import { useAuth } from "../context/AuthContext";
import {
  initials,
  sessionStreak,
  sessionsInLastDays,
  timeAgo,
} from "../lib/activity";
import { LANGUAGES } from "../lib/languages";
import { api } from "../services/api";
import type {
  Conversation,
  DocumentItem,
  Health,
} from "../types";

function greeting() {
  const hour = new Date().getHours();

  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

const QUICK = [
  {
    to: "/tutor",
    title: "AI Tutor",
    text: "Ask questions and understand concepts.",
    icon: GraduationCap,
    label: "Learn",
    soon: false,
  },
  {
    to: "/code",
    title: "Orin Code",
    text: "Write, run, and improve your code.",
    icon: Code2,
    label: "Code",
    soon: false,
  },
  {
    to: "/practice",
    title: "Practice",
    text: "Build your skills with coding exercises.",
    icon: Target,
    label: "Practice",
    soon: false,
  },
  {
    to: "/documents",
    title: "Documents",
    text: "Learn from your own study materials.",
    icon: FileText,
    label: "Study",
    soon: false,
  },
];

export default function Dashboard() {
  const { user } = useAuth();

  const [health, setHealth] =
    useState<Health | null>(null);
  const [healthErr, setHealthErr] =
    useState("");

  const [convs, setConvs] =
    useState<Conversation[] | null>(null);
  const [convsErr, setConvsErr] =
    useState("");

  const [docCount, setDocCount] =
    useState<number | null>(null);
  const [docsErr, setDocsErr] =
    useState(false);

  const loadHealth = useCallback(() => {
    setHealth(null);
    setHealthErr("");

    api<Health>("/health")
      .then(setHealth)
      .catch((error: Error) =>
        setHealthErr(error.message),
      );
  }, []);

  const loadConversations = useCallback(() => {
    setConvsErr("");

    api<Conversation[]>(
      "/tutor/conversations",
    )
      .then(setConvs)
      .catch((error: Error) =>
        setConvsErr(error.message),
      );
  }, []);

  useEffect(() => {
    loadHealth();
    loadConversations();
  }, [loadHealth, loadConversations]);

  useEffect(() => {
    api<DocumentItem[]>("/documents")
      .then((documents) =>
        setDocCount(documents.length),
      )
      .catch(() => setDocsErr(true));
  }, []);

  const name =
    user?.profile.display_name ?? "";

  const today = new Date().toLocaleDateString(
    undefined,
    {
      weekday: "long",
      day: "numeric",
      month: "short",
    },
  );

  const convState: MetricState = convsErr
    ? "error"
    : convs === null
      ? "loading"
      : "ok";

  const week = convs
    ? sessionsInLastDays(convs, 7)
    : 0;

  const streak = convs
    ? sessionStreak(convs)
    : 0;

  return (
    <div className="relative mx-auto max-w-7xl space-y-8 overflow-hidden p-5 md:p-8">
      {/* Header */}
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1.5 text-xs font-medium text-accent2">
            <Sparkles size={13} />
            Your learning workspace
          </div>

          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            {greeting()}, {name}.
          </h1>

          <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400 md:text-base">
            Continue learning, build something,
            and make progress today.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-xl border border-line bg-panel/50 px-3.5 py-2.5 text-xs text-slate-400 sm:flex">
            <Calendar size={14} />
            {today}
          </div>

          <div
            aria-label={`Signed in as ${name}`}
            className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-accent to-accent2 text-sm font-bold text-slate-950 shadow-lg shadow-accent/10"
          >
            {initials(name)}
          </div>
        </div>
      </header>

      {/* Main hero */}
      <section className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-gradient-to-br from-accent/[0.10] via-panel to-panel p-6 shadow-xl shadow-black/10 md:p-8">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-28 -top-28 h-80 w-80 rounded-full border border-accent/10"
        />

        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full border border-accent/10"
        />

        <div
          aria-hidden="true"
          className="pointer-events-none absolute right-8 top-8 h-3 w-3 rounded-full bg-accent shadow-lg shadow-accent/50"
        />

        <div className="relative grid gap-8 lg:grid-cols-[1fr_280px] lg:items-center">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent2">
              <Languages size={13} />
              Learn in your language
            </div>

            <h2 className="mt-5 text-3xl font-bold leading-tight tracking-tight md:text-4xl">
              Learn.
              <span className="text-accent">
                {" "}
                Code.
              </span>
              <br />
              Evolve.
            </h2>

            <p className="mt-4 max-w-xl text-sm leading-7 text-slate-300 md:text-base">
              Orin brings your AI tutor, coding
              environment, practice problems, and
              learning materials together in one
              focused workspace.
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                to="/tutor"
                className="group inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-accent/15 transition hover:brightness-110"
              >
                Start Learning
                <ArrowRight
                  size={16}
                  className="transition-transform group-hover:translate-x-0.5"
                />
              </Link>

              <Link
                to="/code"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/[0.07]"
              >
                Open Orin Code
                <Code2 size={16} />
              </Link>
            </div>
          </div>

          {/* Learning loop */}
          <div className="hidden rounded-2xl border border-white/[0.08] bg-black/10 p-5 lg:block">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
              Your workflow
            </p>

            <div className="mt-5 space-y-3">
              <JourneyStep
                icon={BookOpen}
                label="Learn"
                text="Understand"
                active
              />

              <JourneyStep
                icon={Code2}
                label="Code"
                text="Build"
              />

              <JourneyStep
                icon={Target}
                label="Practice"
                text="Test"
              />

              <JourneyStep
                icon={TrendingUp}
                label="Improve"
                text="Evolve"
              />
            </div>
          </div>
        </div>
      </section>

      {/* AI + real metrics */}
      <div className="grid gap-4 lg:grid-cols-3">
        <section className="grid grid-cols-2 gap-3 lg:col-span-2 lg:grid-cols-4">
          <MetricCard
            icon={MessageSquare}
            label="Learning Sessions"
            state={convState}
            value={convs?.length ?? 0}
            caption={
              week > 0
                ? `${week} in the last 7 days`
                : "Tutor conversations"
            }
          />

          <MetricCard
            icon={Code2}
            label="Coding"
            state="ok"
            value="Explore"
            caption="Practice in Orin Code"
          />

          <MetricCard
            icon={FileText}
            label="Documents"
            state={
              docsErr
                ? "error"
                : docCount === null
                  ? "loading"
                  : "ok"
            }
            value={docCount ?? 0}
            caption="Study materials"
          />

          <MetricCard
            icon={Flame}
            label="Learning Streak"
            state={convState}
            value={`${streak} ${
              streak === 1
                ? "day"
                : "days"
            }`}
            caption="Tutor activity"
          />
        </section>

        <AiStatusCard
          health={health}
          error={healthErr}
          onRetry={loadHealth}
        />
      </div>

      {/* Quick access */}
      <section>
        <div className="mb-4 flex items-end justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
              Workspace
            </p>

            <h2 className="mt-1 text-xl font-semibold tracking-tight">
              Continue Learning
            </h2>
          </div>

          <Link
            to="/progress"
            className="hidden items-center gap-1 text-xs font-medium text-accent2 transition hover:brightness-125 sm:flex"
          >
            View progress
            <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {QUICK.map(
            ({
              to,
              title,
              text,
              icon: Icon,
              label,
            }) => (
              <Link
                key={to}
                to={to}
                className="group relative overflow-hidden rounded-2xl border border-white/[0.07] bg-panel/60 p-5 transition duration-200 hover:-translate-y-0.5 hover:border-accent/20 hover:bg-panel"
              >
                <div className="flex items-start justify-between">
                  <div className="grid h-11 w-11 place-items-center rounded-xl bg-accent/10 text-accent transition group-hover:bg-accent/15">
                    <Icon size={20} />
                  </div>

                  <ArrowUpRight
                    size={17}
                    className="text-slate-600 transition group-hover:text-accent2"
                  />
                </div>

                <div className="mt-5">
                  <span className="text-[10px] font-medium uppercase tracking-[0.16em] text-slate-600">
                    {label}
                  </span>

                  <h3 className="mt-1 font-semibold">
                    {title}
                  </h3>

                  <p className="mt-1.5 text-sm leading-5 text-slate-400">
                    {text}
                  </p>
                </div>
              </Link>
            ),
          )}
        </div>
      </section>

      {/* Journey + recent activity */}
      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-2xl border border-white/[0.07] bg-panel/60 p-5 md:p-6 lg:col-span-2">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <TrendingUp
                  size={18}
                  className="text-accent"
                />

                <h2 className="text-lg font-semibold">
                  Your Learning Journey
                </h2>
              </div>

              <p className="mt-1 text-sm text-slate-500">
                Real progress will appear here as
                you complete coding and practice
                activities.
              </p>
            </div>

            <Link
              to="/progress"
              className="hidden rounded-lg border border-white/10 px-3 py-2 text-xs font-medium text-slate-300 transition hover:bg-white/5 sm:block"
            >
              Progress
            </Link>
          </div>

          <div className="mt-6">
            <EmptyState
              icon={TrendingUp}
              title="Build your learning history"
              text="Complete coding or practice activities to turn your learning journey into measurable progress."
              actionLabel="Start practicing"
              to="/practice"
            />
          </div>
        </section>

        <section className="rounded-2xl border border-white/[0.07] bg-panel/60 p-5 md:p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <History
                  size={18}
                  className="text-accent"
                />

                <h2 className="text-lg font-semibold">
                  Recent Activity
                </h2>
              </div>

              <p className="mt-1 text-xs text-slate-500">
                Your latest tutor sessions
              </p>
            </div>
          </div>

          {convsErr && (
            <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-300">
              {convsErr}
            </div>
          )}

          {!convs && !convsErr && (
            <div className="mt-5 space-y-2">
              {[0, 1, 2].map((item) => (
                <div
                  key={item}
                  className="h-12 animate-pulse rounded-xl bg-white/5"
                />
              ))}
            </div>
          )}

          {convs && convs.length === 0 && (
            <div className="mt-4">
              <EmptyState
                icon={MessageSquare}
                title="No activity yet"
                text="Your tutor conversations will appear here."
                actionLabel="Ask the tutor"
                to="/tutor"
              />
            </div>
          )}

          {convs && convs.length > 0 && (
            <ul className="mt-4 space-y-1">
              {convs.slice(0, 4).map((conversation) => (
                <li key={conversation.id}>
                  <Link
                    to={`/tutor?c=${conversation.id}`}
                    className="group flex items-center gap-3 rounded-xl px-2 py-2.5 transition hover:bg-white/[0.04]"
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white/5 text-slate-400 transition group-hover:text-accent">
                      <MessageSquare
                        size={15}
                      />
                    </span>

                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-slate-200">
                        {conversation.title}
                      </span>

                      <span className="mt-0.5 block text-xs text-slate-500">
                        {timeAgo(
                          conversation.created_at,
                        )}{" "}
                        ·{" "}
                        {LANGUAGES.find(
                          (language) =>
                            language.code ===
                            conversation.language,
                        )?.label ??
                          conversation.language}
                      </span>
                    </span>

                    <ArrowUpRight
                      size={14}
                      className="text-slate-700 transition group-hover:text-slate-400"
                    />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {/* Bottom product statement */}
      <section className="rounded-2xl border border-white/[0.06] bg-white/[0.02] px-5 py-5 md:px-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-accent/10 text-accent">
              <CheckCircle2 size={17} />
            </div>

            <div>
              <p className="text-sm font-medium text-slate-200">
                One workspace for learning and building.
              </p>

              <p className="mt-1 text-xs leading-5 text-slate-500">
                Learn concepts with your tutor,
                practice deliberately, and write
                real code with Orin.
              </p>
            </div>
          </div>

          <Link
            to="/code"
            className="inline-flex shrink-0 items-center gap-2 text-xs font-medium text-accent2 transition hover:brightness-125"
          >
            Open Orin Code
            <ArrowRight size={14} />
          </Link>
        </div>
      </section>
    </div>
  );
}

function JourneyStep({
  icon: Icon,
  label,
  text,
  active = false,
}: {
  icon: typeof BookOpen;
  label: string;
  text: string;
  active?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`grid h-9 w-9 place-items-center rounded-lg ${
          active
            ? "bg-accent/15 text-accent"
            : "bg-white/[0.04] text-slate-500"
        }`}
      >
        <Icon size={16} />
      </div>

      <div className="min-w-0">
        <p className="text-xs font-semibold text-slate-300">
          {label}
        </p>

        <p className="text-[11px] text-slate-600">
          {text}
        </p>
      </div>
    </div>
  );
}