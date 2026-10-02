import {
  Eye,
  EyeOff,
  ArrowRight,
  BookOpen,
  Code2,
  Sparkles,
} from "lucide-react";
import {
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { LanguageSelect } from "../components/LanguageSelect";
import type { Language } from "../types";

export default function AuthPage({
  mode,
}: {
  mode: "login" | "register";
}) {
  const { user, login, register } = useAuth();
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [lang, setLang] =
    useState<Language>("en");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] =
    useState(false);

  if (user) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  const isLogin = mode === "login";

  const submit = async (e: FormEvent) => {
    e.preventDefault();

    setBusy(true);
    setError("");

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(
          email,
          password,
          name,
          lang,
        );
      }

      nav("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-slate-950 text-white">
      {/* Ambient background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
      >
        <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute -bottom-48 -right-40 h-[600px] w-[600px] rounded-full bg-accent2/10 blur-3xl" />

        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      <div className="relative mx-auto grid min-h-screen max-w-7xl lg:grid-cols-2">
        {/* Brand side */}
        <section className="hidden flex-col justify-between px-10 py-10 lg:flex xl:px-16">
          <div>
            <div className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-xl bg-accent text-slate-950 shadow-lg shadow-accent/20">
                <Sparkles
                  size={21}
                  strokeWidth={2.5}
                />
              </div>

              <div>
                <div className="text-xl font-bold tracking-tight">
                  Orin
                </div>
                <div className="text-xs text-slate-500">
                  AI learning workspace
                </div>
              </div>
            </div>
          </div>

          <div className="max-w-xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Learn. Code. Evolve.
            </div>

            <h1 className="text-5xl font-bold leading-[1.08] tracking-tight xl:text-6xl">
              Turn curiosity
              <br />
              into{" "}
              <span className="text-accent">
                capability.
              </span>
            </h1>

            <p className="mt-6 max-w-lg text-base leading-7 text-slate-400">
              A focused learning and coding
              environment that helps you understand
              concepts, practice problems, write code,
              and improve through feedback.
            </p>

            <div className="mt-10 grid max-w-lg grid-cols-3 gap-3">
              <Feature
                icon={<BookOpen size={17} />}
                title="Learn"
                text="Understand concepts"
              />

              <Feature
                icon={<Code2 size={17} />}
                title="Code"
                text="Practice for real"
              />

              <Feature
                icon={<Sparkles size={17} />}
                title="Evolve"
                text="Improve continuously"
              />
            </div>
          </div>

          <p className="text-xs text-slate-600">
            Orin · AI-powered learning workspace
          </p>
        </section>

        {/* Form side */}
        <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-md">
            {/* Mobile brand */}
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-accent text-slate-950">
                <Sparkles
                  size={19}
                  strokeWidth={2.5}
                />
              </div>

              <div>
                <div className="font-bold tracking-tight">
                  Orin
                </div>
                <div className="text-xs text-slate-500">
                  Learn. Code. Evolve.
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.035] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-8">
              <div className="mb-8">
                <div className="mb-3 text-sm font-medium text-accent">
                  {isLogin
                    ? "Welcome back"
                    : "Start your journey"}
                </div>

                <h2 className="text-3xl font-bold tracking-tight">
                  {isLogin
                    ? "Sign in to Orin"
                    : "Create your account"}
                </h2>

                <p className="mt-2 text-sm leading-6 text-slate-400">
                  {isLogin
                    ? "Continue learning where you left off."
                    : "Build your personalized learning workspace."}
                </p>
              </div>

              <form
                onSubmit={submit}
                className="space-y-5"
              >
                {!isLogin && (
                  <div>
                    <label
                      htmlFor="name"
                      className="mb-2 block text-sm font-medium text-slate-300"
                    >
                      Your name
                    </label>

                    <input
                      id="name"
                      className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-accent/60 focus:ring-2 focus:ring-accent/10"
                      placeholder="Enter your name"
                      value={name}
                      onChange={(e) =>
                        setName(e.target.value)
                      }
                      autoComplete="name"
                      required
                    />
                  </div>
                )}

                <div>
                  <label
                    htmlFor="email"
                    className="mb-2 block text-sm font-medium text-slate-300"
                  >
                    Email
                  </label>

                  <input
                    id="email"
                    className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-accent/60 focus:ring-2 focus:ring-accent/10"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) =>
                      setEmail(e.target.value)
                    }
                    autoComplete="email"
                    required
                  />
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label
                      htmlFor="password"
                      className="text-sm font-medium text-slate-300"
                    >
                      Password
                    </label>

                    {isLogin && (
                      <span className="text-xs text-slate-600">
                        Secure sign in
                      </span>
                    )}
                  </div>

                  <div className="relative">
                    <input
                      id="password"
                      className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-4 py-3 pr-12 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-accent/60 focus:ring-2 focus:ring-accent/10"
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      placeholder={
                        isLogin
                          ? "Enter your password"
                          : "At least 8 characters"
                      }
                      minLength={8}
                      maxLength={72}
                      value={password}
                      onChange={(e) =>
                        setPassword(e.target.value)
                      }
                      autoComplete={
                        isLogin
                          ? "current-password"
                          : "new-password"
                      }
                      required
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword(
                          (value) => !value,
                        )
                      }
                      className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-slate-500 transition hover:bg-white/5 hover:text-slate-300"
                      aria-label={
                        showPassword
                          ? "Hide password"
                          : "Show password"
                      }
                    >
                      {showPassword ? (
                        <EyeOff size={18} />
                      ) : (
                        <Eye size={18} />
                      )}
                    </button>
                  </div>
                </div>

                {!isLogin && (
                  <div>
                    <label className="mb-2 block text-sm font-medium text-slate-300">
                      Learning language
                    </label>

                    <LanguageSelect
                      value={lang}
                      onChange={setLang}
                    />
                  </div>
                )}

                {error && (
                  <div
                    role="alert"
                    className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm leading-5 text-red-300"
                  >
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={busy}
                  className="group flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-4 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-accent/10 transition hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {busy ? (
                    <>
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-950/30 border-t-slate-950" />
                      {isLogin
                        ? "Signing in..."
                        : "Creating account..."}
                    </>
                  ) : (
                    <>
                      {isLogin
                        ? "Sign in"
                        : "Create account"}

                      <ArrowRight
                        size={17}
                        className="transition-transform group-hover:translate-x-0.5"
                      />
                    </>
                  )}
                </button>
              </form>

              <div className="my-7 flex items-center gap-3">
                <div className="h-px flex-1 bg-white/[0.07]" />
                <span className="text-[11px] uppercase tracking-wider text-slate-600">
                  Orin
                </span>
                <div className="h-px flex-1 bg-white/[0.07]" />
              </div>

              <p className="text-center text-sm text-slate-500">
                {isLogin ? (
                  <>
                    New to Orin?{" "}
                    <Link
                      className="font-medium text-accent2 transition hover:brightness-125"
                      to="/auth/register"
                    >
                      Create an account
                    </Link>
                  </>
                ) : (
                  <>
                    Already have an account?{" "}
                    <Link
                      className="font-medium text-accent2 transition hover:brightness-125"
                      to="/auth/login"
                    >
                      Sign in
                    </Link>
                  </>
                )}
              </p>
            </div>

            <p className="mt-5 text-center text-xs text-slate-600">
              Your learning workspace starts here.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

function Feature({
  icon,
  title,
  text,
}: {
  icon: React.ReactNode;
  title: string;
  text: string;
}) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-3">
      <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 text-accent">
        {icon}
      </div>

      <div className="text-xs font-semibold text-slate-200">
        {title}
      </div>

      <div className="mt-1 text-[11px] leading-4 text-slate-600">
        {text}
      </div>
    </div>
  );
}