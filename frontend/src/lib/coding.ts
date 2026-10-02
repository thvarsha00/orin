import { api } from "../services/api";

export type CodingLanguage = "python" | "javascript";

export type Status =
  | "passed"
  | "failed"
  | "error"
  | "timeout";

export interface ProblemSummary {
  id: number;
  title: string;
  difficulty: string;
  topic_id: number;
  topic: string;
  language: string;
}

export interface ProblemExample {
  input?: string;
  output?: string;
  explanation?: string;
}

export interface Problem extends ProblemSummary {
  description: string;
  examples: ProblemExample[];
  tags: string[];
  hints: string[];
  constraints: string;
  starter_code: string;
  entry_function: string;
  expected_complexity: string | null;
  visible_tests: number;
  hidden_tests: number;
}

export interface TestResult {
  test_id: number;
  index: number;
  hidden: boolean;
  passed: boolean;
  input: unknown[] | null;
  expected: unknown;
  actual: string | null;
  error: string | null;
  timed_out: boolean;
  time_ms: number;
  stdout: string | null;
}

export interface RunResult {
  status: Status;
  passed: number;
  total: number;
  error: string | null;
  results: TestResult[];
}

export interface SubmitResult extends RunResult {
  submission_id: number;
  execution_time_ms: number;
}

export interface SubmissionItem {
  id: number;
  problem_id: number;
  status: Status;
  passed: number;
  total: number;
  execution_time: number;
  code: string;
  created_at: string;
}

export interface ProgressRecentSubmission {
  problem_id: number;
  status: Status;
  passed: number;
  total: number;
  language: string;
  created_at: string;
}

export interface CodingProgress {
  total_submissions: number;
  problems_attempted: number;
  problems_solved: number;
  tests_passed: number;
  tests_total: number;
  test_accuracy: number;
  python_submissions: number;
  javascript_submissions: number;
  recent_submissions: ProgressRecentSubmission[];
}

export const listProblems = (
  language?: CodingLanguage,
) => {
  const query = language
    ? `?language=${encodeURIComponent(language)}`
    : "";

  return api<ProblemSummary[]>(
    `/coding/problems${query}`,
  );
};

export const getProblem = (id: number) =>
  api<Problem>(`/coding/problems/${id}`);

export const runCode = (
  problem_id: number,
  code: string,
  language: string,
) =>
  api<RunResult>("/coding/run", "POST", {
    problem_id,
    code,
    language,
  });

export const submitCode = (
  problem_id: number,
  code: string,
  language: string,
) =>
  api<SubmitResult>("/coding/submit", "POST", {
    problem_id,
    code,
    language,
  });

export const listSubmissions = (
  problem_id: number,
) =>
  api<SubmissionItem[]>(
    `/coding/problems/${problem_id}/submissions`,
  );

export const getCodingProgress = () =>
  api<CodingProgress>("/coding/progress");

export const MAX_CODE_CHARS = 20_000;

export const STATUS_LABEL: Record<
  Status,
  string
> = {
  passed: "All tests passed",
  failed: "Some tests failed",
  error: "Error",
  timeout: "Time limit exceeded",
};

export const fmt = (v: unknown): string => {
  try {
    return JSON.stringify(v) ?? String(v);
  } catch {
    return String(v);
  }
};

export const formatMs = (ms: number): string =>
  ms < 1
    ? "<1 ms"
    : ms < 1000
      ? `${Math.round(ms)} ms`
      : `${(ms / 1000).toFixed(2)} s`;

const draftKey = (problemId: number) =>
  `orin_code_draft_${problemId}`;

export function loadDraft(
  problemId: number,
): string | null {
  try {
    return localStorage.getItem(
      draftKey(problemId),
    );
  } catch {
    return null;
  }
}

export function saveDraft(
  problemId: number,
  code: string,
): void {
  try {
    localStorage.setItem(
      draftKey(problemId),
      code,
    );
  } catch {
    // Storage unavailable.
  }
}

export function clearDraft(
  problemId: number,
): void {
  try {
    localStorage.removeItem(
      draftKey(problemId),
    );
  } catch {
    // Storage unavailable.
  }
}