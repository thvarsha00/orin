import { useState } from "react";
import {
  Check,
  ChevronRight,
  Globe2,
  GraduationCap,
  Languages,
  Settings2,
  Sparkles,
  UserRound,
} from "lucide-react";

import { LanguageSelect } from "../components/LanguageSelect";
import { ScriptSelect } from "../components/ScriptSelect";
import { useAuth } from "../context/AuthContext";
import type { Level } from "../types";

export default function Settings() {
  const { user, updateProfile } = useAuth();
  const [msg, setMsg] = useState("");

  if (!user) return null;

  const save = async (
    patch: Parameters<typeof updateProfile>[0],
  ) => {
    try {
      setMsg("");
      await updateProfile(patch);
      setMsg("Changes saved");
      window.setTimeout(() => setMsg(""), 2500);
    } catch (e) {
      setMsg((e as Error).message);
    }
  };

    const displayName =
    user.email?.split("@")[0] ||
    "Learner";

  return (
    <div className="min-h-full bg-[#0b0d12] text-slate-100">
      <div className="mx-auto w-full max-w-4xl px-5 py-8 md:px-8 md:py-10">
        {/* Header */}
        <div className="mb-8">
          <div className="mb-5 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]">
              <Settings2 className="h-5 w-5 text-violet-300" />
            </div>

            <div>
              <h1 className="text-xl font-semibold tracking-tight">
                Settings
              </h1>
              <p className="text-sm text-slate-500">
                Configure how Orin works for you.
              </p>
            </div>
          </div>

          {/* Profile row */}
          <div className="flex items-center gap-4 border-b border-white/[0.08] pb-7">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-violet-500/80 to-indigo-500/80 text-lg font-semibold text-white">
              {displayName.charAt(0).toUpperCase()}
            </div>

            <div className="min-w-0">
              <p className="truncate font-medium text-slate-100">
                {displayName}
              </p>
              <p className="truncate text-sm text-slate-500">
                {user.email}
              </p>
            </div>
          </div>
        </div>

        {/* Settings */}
        <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-[#10131a]">
          {/* Learning */}
          <section className="border-b border-white/[0.07]">
            <div className="flex items-start gap-4 px-5 py-5 md:px-6">
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/10">
                <GraduationCap className="h-4 w-4 text-violet-300" />
              </div>

              <div>
                <h2 className="text-sm font-semibold text-slate-100">
                  Learning
                </h2>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Set the language and difficulty level Orin should use.
                </p>
              </div>
            </div>

            <div className="divide-y divide-white/[0.06]">
              {/* Language */}
              <div className="flex flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between md:px-6">
                <div className="flex items-start gap-3">
                  <Globe2 className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />

                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Preferred language
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Used by Orin when communicating with you.
                    </p>
                  </div>
                </div>

                <div className="w-full md:w-56">
                  <LanguageSelect
                    value={user.profile.preferred_language}
                    onChange={(language) =>
                      save({
                        preferred_language: language,
                      })
                    }
                  />
                </div>
              </div>

              {/* Script */}
              {user.profile.preferred_language !== "en" && (
                <div className="flex flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between md:px-6">
                  <div className="flex items-start gap-3">
                    <Languages className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />

                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        Writing script
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        Choose how Orin writes your preferred language.
                      </p>
                    </div>
                  </div>

                  <div className="w-full md:w-56">
                    <ScriptSelect
                      value={user.profile.preferred_script}
                      onChange={(value) =>
                        save({
                          preferred_script: value,
                        })
                      }
                    />
                  </div>
                </div>
              )}

              {/* Skill level */}
              <div className="flex flex-col gap-4 px-5 py-5 md:flex-row md:items-center md:justify-between md:px-6">
                <div className="flex items-start gap-3">
                  <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" />

                  <div>
                    <p className="text-sm font-medium text-slate-200">
                      Skill level
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Helps Orin adjust explanations and learning depth.
                    </p>
                  </div>
                </div>

                <select
                  value={user.profile.skill_level}
                  onChange={(e) =>
                    save({
                      skill_level:
                        e.target.value as Level,
                    })
                  }
                  className="h-9 w-full rounded-lg border border-white/[0.1] bg-[#0b0d12] px-3 text-sm text-slate-200 outline-none transition focus:border-violet-400/50 focus:ring-2 focus:ring-violet-500/10 md:w-56"
                >
                  <option value="beginner">
                    Beginner
                  </option>
                  <option value="intermediate">
                    Intermediate
                  </option>
                  <option value="advanced">
                    Advanced
                  </option>
                </select>
              </div>
            </div>
          </section>

          {/* Account */}
          <section>
            <div className="flex items-start gap-4 px-5 py-5 md:px-6">
              <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/[0.04]">
                <UserRound className="h-4 w-4 text-slate-400" />
              </div>

              <div className="flex-1">
                <h2 className="text-sm font-semibold text-slate-100">
                  Account
                </h2>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Your Orin account information.
                </p>
              </div>
            </div>

            <div className="border-t border-white/[0.06]">
              <div className="flex items-center justify-between px-5 py-5 md:px-6">
                <div>
                  <p className="text-sm font-medium text-slate-200">
                    Account email
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {user.email}
                  </p>
                </div>

                <ChevronRight className="h-4 w-4 text-slate-600" />
              </div>
            </div>
          </section>
        </div>

        {/* Save status */}
        <div className="mt-4 flex min-h-6 items-center justify-end">
          {msg && (
            <div
              className={`flex items-center gap-2 text-xs ${
                msg === "Changes saved"
                  ? "text-emerald-400"
                  : "text-red-400"
              }`}
            >
              {msg === "Changes saved" && (
                <Check className="h-3.5 w-3.5" />
              )}
              <span>{msg}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}