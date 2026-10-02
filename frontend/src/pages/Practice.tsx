import {
  ArrowRight,
  BookOpen,
  Code2,
  Flame,
  Gauge,
  Play,
  Sparkles,
  Target,
  Trophy,
  Zap,
} from "lucide-react";
import { Link } from "react-router-dom";

const MODES = [
  {
    icon: Target,
    title: "Daily Challenge",
    description:
      "Pick a coding problem and give yourself a focused challenge.",
    label: "1 challenge",
    href: "/code",
    accent: "text-rose-300",
    background: "bg-rose-400/10",
    border: "border-rose-400/20",
  },
  {
    icon: Zap,
    title: "Quick Practice",
    description:
      "Jump straight into the coding path and solve problems at your pace.",
    label: "120 problems",
    href: "/code",
    accent: "text-accent",
    background: "bg-accent/10",
    border: "border-accent/20",
  },
  {
    icon: Gauge,
    title: "Build Your Skills",
    description:
      "Start with fundamentals and gradually move toward harder algorithms.",
    label: "12 levels",
    href: "/code",
    accent: "text-amber-300",
    background: "bg-amber-400/10",
    border: "border-amber-400/20",
  },
];

const DIFFICULTIES = [
  {
    name: "Easy",
    description: "Build your foundations",
    count: "40",
    accent: "text-emerald-300",
    background: "bg-emerald-400/10",
    border: "border-emerald-400/20",
    dot: "bg-emerald-400",
  },
  {
    name: "Medium",
    description: "Strengthen your logic",
    count: "50",
    accent: "text-amber-300",
    background: "bg-amber-400/10",
    border: "border-amber-400/20",
    dot: "bg-amber-400",
  },
  {
    name: "Hard",
    description: "Challenge your limits",
    count: "30",
    accent: "text-rose-300",
    background: "bg-rose-400/10",
    border: "border-rose-400/20",
    dot: "bg-rose-400",
  },
];

export default function Practice() {
  return (
    <div className="mx-auto max-w-5xl p-4 md:p-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border border-line bg-slate-950/70 p-6 shadow-2xl md:p-10">
        <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-accent/10 blur-3xl" />

        <div className="pointer-events-none absolute -bottom-32 -right-20 h-80 w-80 rounded-full bg-violet-500/10 blur-3xl" />

        <div className="relative">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.18em] text-accent">
            <Sparkles size={13} />
            Practice Arena
          </div>

          <div className="mt-6 flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <h1 className="text-3xl font-black tracking-tight text-white md:text-5xl">
                Sharpen your
                <span className="text-accent">
                  {" "}coding skills.
                </span>
              </h1>

              <p className="mt-4 max-w-xl text-sm leading-7 text-slate-400 md:text-base">
                Practice without pressure. Choose a challenge,
                write your solution, run your code, and learn from
                every attempt.
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-3">
              <div className="rounded-2xl border border-line bg-slate-900/70 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Code2
                    size={14}
                    className="text-accent"
                  />

                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Problems
                  </span>
                </div>

                <p className="mt-1 text-2xl font-black text-white">
                  120
                </p>
              </div>

              <div className="rounded-2xl border border-line bg-slate-900/70 px-4 py-3">
                <div className="flex items-center gap-2">
                  <Trophy
                    size={14}
                    className="text-amber-300"
                  />

                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    Levels
                  </span>
                </div>

                <p className="mt-1 text-2xl font-black text-white">
                  12
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main action */}
      <section className="mt-6">
        <Link
          to="/code"
          className="group relative block overflow-hidden rounded-3xl border border-accent/20 bg-gradient-to-br from-accent/10 via-slate-950/80 to-slate-950 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-accent/40 hover:shadow-2xl hover:shadow-accent/5 md:p-8"
        >
          <div className="pointer-events-none absolute -right-16 -top-20 h-56 w-56 rounded-full bg-accent/10 blur-3xl transition group-hover:bg-accent/20" />

          <div className="relative flex flex-col gap-7 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-5">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-accent/20 bg-accent/10">
                <Play
                  size={27}
                  fill="currentColor"
                  className="text-accent"
                />
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-black uppercase tracking-[0.2em] text-accent">
                    Ready?
                  </span>

                  <span className="h-1 w-1 rounded-full bg-slate-700" />

                  <span className="text-xs text-slate-600">
                    Coding Arena
                  </span>
                </div>

                <h2 className="mt-2 text-2xl font-black text-white">
                  Continue your coding journey
                </h2>

                <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
                  Choose Python or JavaScript and follow
                  the level-based path from fundamentals
                  to advanced problems.
                </p>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2 text-sm font-bold text-accent">
              Start coding

              <ArrowRight
                size={17}
                className="transition-transform group-hover:translate-x-1"
              />
            </div>
          </div>
        </Link>
      </section>

      {/* Practice modes */}
      <section className="mt-10">
        <div className="mb-4 flex items-end justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
              Practice modes
            </p>

            <h2 className="mt-1 text-xl font-bold text-white">
              How do you want to practice?
            </h2>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {MODES.map((mode) => {
            const Icon = mode.icon;

            return (
              <Link
                key={mode.title}
                to={mode.href}
                className="group rounded-3xl border border-line bg-slate-950/60 p-5 transition-all duration-300 hover:-translate-y-1 hover:border-slate-600 hover:bg-slate-900/80 hover:shadow-xl"
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-2xl border ${mode.border} ${mode.background}`}
                >
                  <Icon
                    size={21}
                    className={mode.accent}
                  />
                </div>

                <h3 className="mt-5 text-lg font-bold text-white">
                  {mode.title}
                </h3>

                <p className="mt-2 min-h-[48px] text-sm leading-6 text-slate-500">
                  {mode.description}
                </p>

                <div className="mt-5 flex items-center justify-between border-t border-line pt-4">
                  <span className="text-xs font-semibold text-slate-600">
                    {mode.label}
                  </span>

                  <ArrowRight
                    size={15}
                    className="text-slate-700 transition-all group-hover:translate-x-1 group-hover:text-accent"
                  />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Difficulty */}
      <section className="mt-10">
        <div className="mb-4">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-600">
            Difficulty
          </p>

          <h2 className="mt-1 text-xl font-bold text-white">
            Choose your challenge
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {DIFFICULTIES.map((difficulty) => (
            <Link
              key={difficulty.name}
              to="/code"
              className={`group rounded-3xl border bg-slate-950/60 p-5 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${difficulty.border}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span
                    className={`h-3 w-3 rounded-full ${difficulty.dot}`}
                  />

                  <h3
                    className={`font-bold ${difficulty.accent}`}
                  >
                    {difficulty.name}
                  </h3>
                </div>

                <span className="text-2xl font-black text-white">
                  {difficulty.count}
                </span>
              </div>

              <p className="mt-4 text-sm text-slate-500">
                {difficulty.description}
              </p>

              <div className="mt-5 flex items-center justify-between border-t border-line pt-4">
                <span className="text-xs font-medium text-slate-600">
                  Explore problems
                </span>

                <ArrowRight
                  size={15}
                  className="text-slate-700 transition-all group-hover:translate-x-1 group-hover:text-accent"
                />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Learning philosophy */}
      <section className="mt-10 grid gap-4 md:grid-cols-2">
        <div className="rounded-3xl border border-line bg-slate-950/60 p-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-sky-400/20 bg-sky-400/10">
            <BookOpen
              size={20}
              className="text-sky-300"
            />
          </div>

          <h2 className="mt-5 text-lg font-bold text-white">
            Practice by doing
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Don't just read about algorithms. Write the
            code, run it against tests, inspect the result,
            and improve your solution.
          </p>
        </div>

        <div className="rounded-3xl border border-line bg-slate-950/60 p-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-orange-400/20 bg-orange-400/10">
            <Flame
              size={20}
              className="text-orange-300"
            />
          </div>

          <h2 className="mt-5 text-lg font-bold text-white">
            Progress comes from consistency
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Solve a little today, then come back tomorrow.
            Your future progress system will track your
            completed challenges and learning streaks here.
          </p>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="mt-10 mb-4 rounded-3xl border border-line bg-slate-950/60 p-8 text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-accent/20 bg-accent/10">
          <Sparkles
            size={24}
            className="text-accent"
          />
        </div>

        <h2 className="mt-5 text-xl font-black text-white">
          Ready to write some code?
        </h2>

        <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
          Pick a language, choose your level, and
          start solving.
        </p>

        <Link
          to="/code"
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-3 text-sm font-bold text-white shadow-lg shadow-accent/10 transition hover:-translate-y-0.5 hover:brightness-110"
        >
          <Code2 size={16} />
          Open Orin Code
        </Link>
      </section>
    </div>
  );
}