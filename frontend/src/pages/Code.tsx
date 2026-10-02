import {
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  useNavigate,
} from "react-router-dom";

import {
  getCodingProgress,
  listProblems,
  type CodingProgress,
  type CodingLanguage,
  type ProblemSummary,
} from "../lib/coding";

type Difficulty =
  | "all"
  | "easy"
  | "medium"
  | "hard";

const difficultyOrder: Record<string, number> = {
  easy: 1,
  medium: 2,
  hard: 3,
};

const difficultyColor = (
  difficulty: string,
) => {
  if (difficulty === "easy") {
    return "#22c55e";
  }

  if (difficulty === "medium") {
    return "#f59e0b";
  }

  if (difficulty === "hard") {
    return "#ef4444";
  }

  return "#94a3b8";
};

const languageLabels: Record<
  CodingLanguage,
  string
> = {
  python: "Python",
  javascript: "JavaScript",
};

export default function Code() {
  const navigate = useNavigate();

  const [language, setLanguage] =
    useState<CodingLanguage>("javascript");

  const [problems, setProblems] = useState<
    ProblemSummary[]
  >([]);

  const [progress, setProgress] =
    useState<CodingProgress | null>(null);

  const [search, setSearch] =
    useState("");

  const [difficulty, setDifficulty] =
    useState<Difficulty>("all");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const [
          problemData,
          progressData,
        ] = await Promise.all([
          listProblems(language),
          getCodingProgress(),
        ]);

        if (cancelled) {
          return;
        }

        setProblems(problemData);
        setProgress(progressData);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load coding problems.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [language]);

  const filteredProblems = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    return [...problems]
      .filter((problem) => {
        if (
          difficulty !== "all" &&
          problem.difficulty.toLowerCase() !==
            difficulty
        ) {
          return false;
        }

        if (!query) {
          return true;
        }

        return (
          problem.title
            .toLowerCase()
            .includes(query) ||
          problem.topic
            .toLowerCase()
            .includes(query)
        );
      })
      .sort((a, b) => {
        const difficultyDifference =
          (difficultyOrder[
            a.difficulty.toLowerCase()
          ] ?? 99) -
          (difficultyOrder[
            b.difficulty.toLowerCase()
          ] ?? 99);

        if (difficultyDifference !== 0) {
          return difficultyDifference;
        }

        return a.id - b.id;
      });
  }, [
    problems,
    search,
    difficulty,
  ]);

  const easyCount = problems.filter(
    (problem) =>
      problem.difficulty.toLowerCase() ===
      "easy",
  ).length;

  const mediumCount = problems.filter(
    (problem) =>
      problem.difficulty.toLowerCase() ===
      "medium",
  ).length;

  const hardCount = problems.filter(
    (problem) =>
      problem.difficulty.toLowerCase() ===
      "hard",
  ).length;

  const solvedCount =
    progress?.problems_solved ?? 0;

  const attemptedCount =
    progress?.problems_attempted ?? 0;

  const accuracy =
    progress?.test_accuracy ?? 0;

  const totalProblems = problems.length;

  return (
    <div
      style={{
        minHeight: "100%",
        background: "#0b0d12",
        color: "#e5e7eb",
        padding: "28px 32px 48px",
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
        }}
      >
        {/* Header */}
        <header
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: 24,
            marginBottom: 28,
          }}
        >
          <div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                marginBottom: 8,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: "#8b5cf6",
                  boxShadow:
                    "0 0 12px rgba(139,92,246,.65)",
                }}
              />

              <span
                style={{
                  color: "#a78bfa",
                  fontSize: 12,
                  fontWeight: 700,
                  letterSpacing: ".12em",
                  textTransform: "uppercase",
                }}
              >
                Orin Code
              </span>
            </div>

            <h1
              style={{
                margin: 0,
                fontSize: 30,
                lineHeight: 1.2,
                fontWeight: 700,
                letterSpacing: "-.03em",
                color: "#f8fafc",
              }}
            >
              Coding problems
            </h1>

            <p
              style={{
                margin:
                  "8px 0 0",
                color: "#8b93a3",
                fontSize: 14,
              }}
            >
              Solve problems, practice patterns,
              and improve through code.
            </p>
          </div>

          <select
            value={language}
            onChange={(event) =>
              setLanguage(
                event.target
                  .value as CodingLanguage,
              )
            }
            style={{
              height: 38,
              minWidth: 145,
              padding: "0 12px",
              border:
                "1px solid #252a35",
              borderRadius: 7,
              background: "#11141a",
              color: "#e5e7eb",
              outline: "none",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            {(
              Object.keys(
                languageLabels,
              ) as CodingLanguage[]
            ).map((value) => (
              <option
                key={value}
                value={value}
              >
                {languageLabels[value]}
              </option>
            ))}
          </select>
        </header>

        {/* Compact stats */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 0,
            height: 68,
            marginBottom: 26,
            borderTop:
              "1px solid #20242d",
            borderBottom:
              "1px solid #20242d",
          }}
        >
          <Stat
            label="Problems"
            value={totalProblems}
          />

          <Stat
            label="Easy"
            value={easyCount}
            valueColor="#22c55e"
          />

          <Stat
            label="Medium"
            value={mediumCount}
            valueColor="#f59e0b"
          />

          <Stat
            label="Hard"
            value={hardCount}
            valueColor="#ef4444"
          />

          <Stat
            label="Solved"
            value={solvedCount}
            valueColor="#a78bfa"
          />

          <Stat
            label="Accuracy"
            value={`${accuracy}%`}
            valueColor="#a78bfa"
          />
        </div>

        {/* Progress line */}
        {progress && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              marginBottom: 22,
              color: "#737b8c",
              fontSize: 12,
            }}
          >
            <span>
              {attemptedCount} problems attempted
            </span>

            <span
              style={{
                color: "#3b4250",
              }}
            >
              ·
            </span>

            <span>
              {progress.total_submissions} submissions
            </span>

            <span
              style={{
                color: "#3b4250",
              }}
            >
              ·
            </span>

            <span>
              {progress.tests_passed}/
              {progress.tests_total} tests passed
            </span>
          </div>
        )}

        {/* Search / filters */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            marginBottom: 14,
          }}
        >
          <div
            style={{
              position: "relative",
              flex: 1,
            }}
          >
            <span
              style={{
                position: "absolute",
                left: 13,
                top: "50%",
                transform:
                  "translateY(-50%)",
                color: "#687080",
                fontSize: 15,
              }}
            >
              ⌕
            </span>

            <input
              value={search}
              onChange={(event) =>
                setSearch(
                  event.target.value,
                )
              }
              placeholder="Search problems..."
              style={{
                width: "100%",
                height: 40,
                boxSizing: "border-box",
                padding:
                  "0 14px 0 38px",
                border:
                  "1px solid #252a35",
                borderRadius: 7,
                background: "#11141a",
                color: "#e5e7eb",
                outline: "none",
                fontSize: 13,
              }}
            />
          </div>

          <DifficultyButton
            active={difficulty === "all"}
            onClick={() =>
              setDifficulty("all")
            }
          >
            All
          </DifficultyButton>

          <DifficultyButton
            active={difficulty === "easy"}
            color="#22c55e"
            onClick={() =>
              setDifficulty("easy")
            }
          >
            Easy
          </DifficultyButton>

          <DifficultyButton
            active={difficulty === "medium"}
            color="#f59e0b"
            onClick={() =>
              setDifficulty("medium")
            }
          >
            Medium
          </DifficultyButton>

          <DifficultyButton
            active={difficulty === "hard"}
            color="#ef4444"
            onClick={() =>
              setDifficulty("hard")
            }
          >
            Hard
          </DifficultyButton>
        </div>

        {/* Problem table */}
        <div
          style={{
            borderTop:
              "1px solid #252a35",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "minmax(320px, 1fr) 190px 110px 70px",
              alignItems: "center",
              minHeight: 42,
              padding: "0 16px",
              borderBottom:
                "1px solid #20242d",
              color: "#626b7b",
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: ".08em",
              textTransform: "uppercase",
            }}
          >
            <span>Problem</span>
            <span>Topic</span>
            <span>Difficulty</span>
            <span />
          </div>

          {loading && (
            <div
              style={{
                padding: "42px 16px",
                color: "#737b8c",
                fontSize: 14,
              }}
            >
              Loading problems...
            </div>
          )}

          {!loading && error && (
            <div
              style={{
                padding: "42px 16px",
                color: "#f87171",
                fontSize: 14,
              }}
            >
              {error}
            </div>
          )}

          {!loading &&
            !error &&
            filteredProblems.length === 0 && (
              <div
                style={{
                  padding: "42px 16px",
                  color: "#737b8c",
                  fontSize: 14,
                }}
              >
                No problems match your filters.
              </div>
            )}

          {!loading &&
            !error &&
            filteredProblems.map(
              (problem, index) => (
                <button
                  key={problem.id}
                  type="button"
                  onClick={() =>
                    navigate(
                      `/code/${problem.id}`,
                    )
                  }
                  style={{
                    width: "100%",
                    display: "grid",
                    gridTemplateColumns:
                      "minmax(320px, 1fr) 190px 110px 70px",
                    alignItems: "center",
                    minHeight: 58,
                    padding: "0 16px",
                    border: "none",
                    borderBottom:
                      "1px solid #1b1f27",
                    background:
                      index % 2 === 0
                        ? "#0b0d12"
                        : "#0e1117",
                    color: "#e5e7eb",
                    textAlign: "left",
                    cursor: "pointer",
                    transition:
                      "background .15s ease",
                  }}
                  onMouseEnter={(event) => {
                    event.currentTarget.style.background =
                      "#151922";
                  }}
                  onMouseLeave={(event) => {
                    event.currentTarget.style.background =
                      index % 2 === 0
                        ? "#0b0d12"
                        : "#0e1117";
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 12,
                      minWidth: 0,
                    }}
                  >
                    <span
                      style={{
                        width: 24,
                        color: "#4f5868",
                        fontSize: 12,
                        fontVariantNumeric:
                          "tabular-nums",
                      }}
                    >
                      {String(
                        index + 1,
                      ).padStart(2, "0")}
                    </span>

                    <span
                      style={{
                        overflow: "hidden",
                        textOverflow:
                          "ellipsis",
                        whiteSpace:
                          "nowrap",
                        fontSize: 14,
                        fontWeight: 500,
                        color: "#e8ebf0",
                      }}
                    >
                      {problem.title}
                    </span>
                  </div>

                  <span
                    style={{
                      overflow: "hidden",
                      textOverflow:
                        "ellipsis",
                      whiteSpace:
                        "nowrap",
                      color: "#737b8c",
                      fontSize: 12,
                    }}
                  >
                    {problem.topic}
                  </span>

                  <span
                    style={{
                      color: difficultyColor(
                        problem.difficulty.toLowerCase(),
                      ),
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {capitalize(
                      problem.difficulty,
                    )}
                  </span>

                  <span
                    style={{
                      color: "#626b7b",
                      fontSize: 17,
                      textAlign: "right",
                    }}
                  >
                    →
                  </span>
                </button>
              ),
            )}
        </div>

        {/* Footer */}
        {!loading &&
          !error &&
          filteredProblems.length > 0 && (
            <div
              style={{
                padding:
                  "16px 4px 0",
                color: "#596273",
                fontSize: 12,
              }}
            >
              Showing {filteredProblems.length}{" "}
              of {problems.length} problems
            </div>
          )}
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  valueColor = "#e5e7eb",
}: {
  label: string;
  value: number | string;
  valueColor?: string;
}) {
  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        gap: 4,
        padding: "0 20px",
        borderRight:
          "1px solid #20242d",
      }}
    >
      <span
        style={{
          color: "#626b7b",
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: ".08em",
          fontWeight: 700,
        }}
      >
        {label}
      </span>

      <span
        style={{
          color: valueColor,
          fontSize: 17,
          fontWeight: 650,
          fontVariantNumeric:
            "tabular-nums",
        }}
      >
        {value}
      </span>
    </div>
  );
}

function DifficultyButton({
  active,
  color,
  onClick,
  children,
}: {
  active: boolean;
  color?: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        height: 40,
        padding: "0 13px",
        border: active
          ? `1px solid ${
              color ?? "#8b5cf6"
            }`
          : "1px solid #252a35",
        borderRadius: 7,
        background: active
          ? "#151922"
          : "#11141a",
        color: active
          ? color ?? "#c4b5fd"
          : "#8b93a3",
        fontSize: 12,
        fontWeight: 600,
        cursor: "pointer",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </button>
  );
}

function capitalize(
  value: string,
) {
  return (
    value.charAt(0).toUpperCase() +
    value.slice(1).toLowerCase()
  );
}