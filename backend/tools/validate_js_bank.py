"""
Validate the Orin JavaScript problem bank. READ-ONLY.

  python .\tools\validate_js_bank.py --self-test
  python .\tools\validate_js_bank.py --source bank --expect 1
  python .\tools\validate_js_bank.py --source parts --partial
  python .\tools\validate_js_bank.py --source parts            (final: 6 parts x 20 = 120)

WARNING: this runs OUR OWN trusted reference solutions in a local Node
subprocess through the project's real executor. It is NOT a secure sandbox.
Never point it at JavaScript you did not write.

It never writes any file and never opens the database. Hidden tests are not
printed unless --show-hidden is passed (local debugging only).

Exit codes: 0 = pass, 1 = validation failures, 2 = environment/usage error.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import json
import math
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services.coding.evaluator import TestSpec, evaluate, values_equal  # noqa: E402
from app.services.coding.executor import RunnerUnavailable, run_code  # noqa: E402

PARTS_DIR = BACKEND / "tools" / "js_bank"
BANK_PATH = BACKEND / "app" / "services" / "coding" / "problem_bank" / "javascript.json"
PY_BANK_PATH = BACKEND / "app" / "services" / "coding" / "problem_bank" / "python.json"

PART_NAMES = [f"part{n:02d}.json" for n in range(1, 7)]
PER_PART = 20
DIFFICULTIES = {"easy", "medium", "hard"}
TARGET_SPLIT = {"easy": 40, "medium": 50, "hard": 30}
MIN_TAGS = 2
MIN_HINTS = 2
SIZE_LIMIT = 3500  # executor stores roughly 4000 chars of result JSON

SOLVE_RE = re.compile(r"\bfunction\s+solve\s*\(")
FORBIDDEN_RE = re.compile(
    r"\brequire\b|\bprocess\b|\beval\b|new\s+Function|\basync\b|\bawait\b|"
    r"\bPromise\b|Math\.random|\bDate\b|\bsetTimeout\b|\bsetInterval\b|\bsetImmediate\b"
)

STRICT_JS = r"""
function __orin_check(v, p) {
    if (v === null || typeof v === "boolean" || typeof v === "string") { return; }
    if (typeof v === "number") {
        if (!Number.isFinite(v)) { throw new Error("STRICT: non-finite number at " + p); }
        if (Object.is(v, -0)) { throw new Error("STRICT: negative zero at " + p); }
        if (Number.isInteger(v) && !Number.isSafeInteger(v)) {
            throw new Error("STRICT: unsafe integer at " + p);
        }
        return;
    }
    if (Array.isArray(v)) {
        for (let i = 0; i < v.length; i++) {
            if (!(i in v)) { throw new Error("STRICT: array hole at " + p + "[" + i + "]"); }
            __orin_check(v[i], p + "[" + i + "]");
        }
        return;
    }
    if (typeof v === "object") {
        const proto = Object.getPrototypeOf(v);
        if (proto !== Object.prototype && proto !== null) {
            throw new Error("STRICT: non-plain object at " + p);
        }
        for (const k of Object.keys(v)) { __orin_check(v[k], p + "." + k); }
        return;
    }
    throw new Error("STRICT: unsupported type " + typeof v + " at " + p);
}
function __orin_strict(...args) {
    const v = solve(...args);
    __orin_check(v, "result");
    return v;
}
"""


# ---------------------------------------------------------------- helpers

def _reject_constant(name):
    raise ValueError(f"non-JSON constant {name}")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)


def check_json_safe(v, path="value"):
    """Return an error string if v is not plain JSON-safe data, else None."""
    if v is None or isinstance(v, (bool, str)):
        return None
    if isinstance(v, int):
        if abs(v) > 2**53 - 1:
            return f"{path}: integer outside JS safe range"
        return None
    if isinstance(v, float):
        return None if math.isfinite(v) else f"{path}: non-finite number"
    if isinstance(v, list):
        for i, x in enumerate(v):
            e = check_json_safe(x, f"{path}[{i}]")
            if e:
                return e
        return None
    if isinstance(v, dict):
        for k, x in v.items():
            if not isinstance(k, str):
                return f"{path}: non-string key"
            e = check_json_safe(x, f"{path}.{k}")
            if e:
                return e
        return None
    return f"{path}: unsupported type {type(v).__name__}"


def norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(t).lower()).strip()


def clip(text, n=200) -> str:
    text = str(text)
    return text if len(text) <= n else text[:n] + "..."


def estimate_payload(values) -> int:
    total = 0
    for i, v in enumerate(values):
        total += len(json.dumps(
            {"i": i, "ok": True, "value": v, "ms": 0.12345678901234, "stdout": ""},
            separators=(",", ":"), ensure_ascii=False, default=str))
    return total


# ---------------------------------------------------------------- per-problem

FIELD_TYPES = {
    "title": str, "topic": str, "difficulty": str, "description": str,
    "examples": list, "constraints": str, "starter_code": str,
    "entry_function": str, "expected_complexity": str,
    "tags": list, "hints": list, "tests": list,
}


def validate_schema(p, source):
    """Return (errors, warnings, can_run_reference)."""
    errs, warns = [], []
    if not isinstance(p, dict):
        return ["problem is not a JSON object"], warns, False

    for key, typ in FIELD_TYPES.items():
        if key not in p:
            errs.append(f"missing field '{key}'")
        elif not isinstance(p[key], typ):
            errs.append(f"field '{key}' must be {typ.__name__}")
        elif typ is str and not p[key].strip():
            errs.append(f"field '{key}' is empty")

    ref = p.get("reference_solution")
    if source == "parts":
        if not isinstance(ref, str) or not ref.strip():
            errs.append("missing or empty 'reference_solution'")
    elif "reference_solution" in p:
        errs.append("production bank must not contain 'reference_solution'")

    if isinstance(p.get("difficulty"), str) and p["difficulty"] not in DIFFICULTIES:
        errs.append(f"bad difficulty '{p['difficulty']}' (easy|medium|hard)")

    topic = p.get("topic")
    if isinstance(topic, str) and topic.strip() and not topic.startswith("JavaScript "):
        errs.append("topic must start with 'JavaScript '")

    if p.get("entry_function") != "solve":
        errs.append("entry_function must be exactly 'solve'")

    starter = p.get("starter_code")
    if isinstance(starter, str) and not SOLVE_RE.search(starter):
        errs.append("starter code must define 'function solve('")
    if isinstance(starter, str) and isinstance(ref, str) and starter.strip() == ref.strip():
        errs.append("starter code is identical to the reference solution")

    for name, minimum in (("tags", MIN_TAGS), ("hints", MIN_HINTS)):
        val = p.get(name)
        if isinstance(val, list):
            if not all(isinstance(x, str) and x.strip() for x in val):
                errs.append(f"{name} must contain non-empty strings")
            if len(val) < minimum:
                errs.append(f"{name}: need at least {minimum}, found {len(val)}")

    ex = p.get("examples")
    if isinstance(ex, list):
        if not ex:
            errs.append("examples: need at least 1")
        for i, e in enumerate(ex, 1):
            if not isinstance(e, dict) or not all(
                    isinstance(e.get(k), str) and e.get(k).strip()
                    for k in ("input", "output", "explanation")):
                errs.append(f"example #{i}: needs string input, output, explanation")

    ref_ok = isinstance(ref, str) and bool(ref.strip())
    if source == "parts" and ref_ok:
        if not SOLVE_RE.search(ref):
            errs.append("reference solution must define 'function solve('")
            ref_ok = False
        bad = sorted(set(m.group(0) for m in FORBIDDEN_RE.finditer(ref)))
        if bad:
            errs.append("forbidden construct in reference: " + ", ".join(bad))
            ref_ok = False
        if "console." in ref:
            warns.append("reference uses console.* (captured output counts toward the size cap)")

    tests = p.get("tests")
    tests_ok = isinstance(tests, list) and len(tests) > 0
    if isinstance(tests, list):
        if not tests:
            errs.append("no tests")
        vis = hid = 0
        seen = {}
        outputs = []
        for i, t in enumerate(tests, 1):
            if not isinstance(t, dict):
                errs.append(f"test #{i}: not an object")
                tests_ok = False
                continue
            inp = t.get("input")
            if not isinstance(inp, list):
                errs.append(f"test #{i}: 'input' must be a list of arguments")
                tests_ok = False
            else:
                e = check_json_safe(inp, "input")
                if e:
                    errs.append(f"test #{i}: {e}")
                    tests_ok = False
                key = json.dumps(inp, sort_keys=True, default=str)
                if key in seen:
                    warns.append(f"test #{i} repeats the input of test #{seen[key]}")
                else:
                    seen[key] = i
            if "output" not in t:
                errs.append(f"test #{i}: missing 'output'")
                tests_ok = False
            else:
                e = check_json_safe(t["output"], "output")
                if e:
                    errs.append(f"test #{i}: {e}")
                    tests_ok = False
                outputs.append(t["output"])
            if not isinstance(t.get("hidden"), bool):
                errs.append(f"test #{i}: 'hidden' must be true or false")
                tests_ok = False
            elif t["hidden"]:
                hid += 1
            else:
                vis += 1
        if tests and vis < 1:
            errs.append("needs at least 1 visible test")
        if tests and hid < 1:
            errs.append("needs at least 1 hidden test")
        if 0 < len(tests) < 4:
            warns.append(f"only {len(tests)} tests (4-5 preferred)")
        if outputs:
            est = estimate_payload(outputs)
            if est > SIZE_LIMIT:
                errs.append(f"output size: estimated result payload {est} chars exceeds {SIZE_LIMIT}")

    can_run = source == "parts" and tests_ok and ref_ok
    return errs, warns, can_run


def execute_reference(p, per_case, show_hidden):
    errs, warns = [], []
    tests = p["tests"]
    code = p["reference_solution"] + "\n" + STRICT_JS
    inputs = [t["input"] for t in tests]

    def once():
        return run_code(language="javascript", code=code, entry="__orin_strict",
                        inputs=inputs, runner="subprocess", per_case_seconds=per_case)

    r1 = once()
    if r1.fatal:
        return [f"execution fatal: {clip(r1.fatal)}"], warns
    if len(r1.cases) != len(tests):
        return [f"result count {len(r1.cases)} != test count {len(tests)}"], warns

    specs = [TestSpec(i, t["input"], t["output"], t["hidden"]) for i, t in enumerate(tests)]
    ev = evaluate(specs, r1)
    for k, (t, v) in enumerate(zip(tests, ev.verdicts), 1):
        if v.passed:
            continue
        if t["hidden"] and not show_hidden:
            errs.append(f"hidden test #{k} failed")
            continue
        label = "hidden" if t["hidden"] else "visible"
        if v.error:
            msg = f"test #{k} ({label}) error: {clip(v.error)}"
            if "stopped before" in v.error:
                msg += " (possible timeout, crash, or output cap)"
        else:
            msg = f"test #{k} ({label}) expected {clip(json.dumps(t['output']))}, got {clip(v.actual)}"
        errs.append(msg)

    if not errs:
        r2 = once()
        if r2.fatal or len(r2.cases) != len(r1.cases):
            errs.append("non-deterministic: second run differs in shape")
        else:
            for k, (a, b) in enumerate(zip(r1.cases, r2.cases), 1):
                if not (a.ok and b.ok and values_equal(a.value, b.value)):
                    errs.append(f"non-deterministic: test #{k} differs between runs")
        slow = max((c.time_ms for c in r1.cases), default=0.0)
        if slow > 1000:
            warns.append(f"slowest test took {slow:.0f} ms")
    return errs, warns


def validate_problem(p, source, per_case, show_hidden):
    errs, warns, can_run = validate_schema(p, source)
    if can_run:
        e2, w2 = execute_reference(p, per_case, show_hidden)
        errs += e2
        warns += w2
    return errs, warns


# ---------------------------------------------------------------- bank-level

def load_python_titles():
    try:
        data = load_json(PY_BANK_PATH)
        items = data if isinstance(data, list) else data.get("problems", [])
        return [str(x.get("title", "")) for x in items if isinstance(x, dict)]
    except Exception:
        return []


def check_bank(entries, expect, partial, py_titles):
    errs, warns, info = [], [], []
    probs = [(lbl, p) for lbl, p in entries if isinstance(p, dict)]
    n = len(entries)
    if not partial and n != expect:
        errs.append(f"bank has {n} problems, expected exactly {expect}")
    else:
        info.append(f"problem count: {n}")

    titles = [(lbl, str(p.get("title", "")).strip()) for lbl, p in probs]
    for t, c in Counter(t for _, t in titles).items():
        if c > 1 and t:
            errs.append(f"duplicate title (exact) x{c}: {t!r}")
    groups = {}
    for lbl, t in titles:
        groups.setdefault(norm_title(t), []).append(t)
    for g, ts in groups.items():
        if g and len(ts) > 1 and len(set(ts)) > 1:
            errs.append(f"duplicate title (normalized): {ts}")

    nt = [norm_title(t) for _, t in titles]
    for i in range(len(nt)):
        for j in range(i + 1, len(nt)):
            if nt[i] != nt[j] and difflib.SequenceMatcher(None, nt[i], nt[j]).ratio() > 0.85:
                warns.append(f"near-duplicate titles: {titles[i][1]!r} ~ {titles[j][1]!r}")

    for field, label in (("description", "description"), ("reference_solution", "reference solution")):
        c = Counter(re.sub(r"\s+", " ", str(p.get(field, ""))).strip().lower() for _, p in probs)
        for text, k in c.items():
            if text and k > 1:
                errs.append(f"duplicate {label} x{k}: {clip(text, 60)!r}")

    pyn = {norm_title(t): t for t in py_titles if t}
    for _, t in titles:
        nt1 = norm_title(t)
        if nt1 in pyn:
            warns.append(f"same title as a Python problem: {t!r}")
        else:
            for pn, orig in pyn.items():
                if difflib.SequenceMatcher(None, nt1, pn).ratio() > 0.9:
                    warns.append(f"title very close to Python problem: {t!r} ~ {orig!r}")
                    break

    diff = Counter(str(p.get("difficulty")) for _, p in probs)
    info.append("difficulty: " + ", ".join(f"{k}={diff.get(k, 0)}" for k in ("easy", "medium", "hard"))
                + (f"  (target {TARGET_SPLIT})" if expect == 120 else ""))
    topics = Counter(str(p.get("topic")) for _, p in probs)
    info.append("topics: " + "; ".join(f"{k}={v}" for k, v in sorted(topics.items())))
    return errs, warns, info


# ---------------------------------------------------------------- self-test

def _base():
    return {
        "title": "Self Test Count Positive", "topic": "JavaScript Arrays", "difficulty": "easy",
        "description": "Count the positive numbers.",
        "examples": [{"input": "[1, -2]", "output": "1", "explanation": "One positive."}],
        "constraints": "1 <= n <= 10",
        "starter_code": "function solve(nums) {\n    // write your code here\n}",
        "entry_function": "solve", "expected_complexity": "O(n)",
        "tags": ["arrays", "counting"], "hints": ["Loop once.", "Count x > 0."],
        "reference_solution": "function solve(nums) {\n    let c = 0;\n    for (const x of nums) { if (x > 0) c++; }\n    return c;\n}",
        "tests": [
            {"input": [[1, -2, 3]], "output": 2, "hidden": False},
            {"input": [[-1]], "output": 0, "hidden": False},
            {"input": [[5, 5]], "output": 2, "hidden": True},
            {"input": [[0]], "output": 0, "hidden": True},
        ],
    }


def _mut(**changes):
    p = copy.deepcopy(_base())
    p.update(changes)
    return p


def _ret(body, out):
    return _mut(
        reference_solution="function solve(nums) { " + body + " }",
        tests=[{"input": [[1]], "output": out, "hidden": False},
               {"input": [[2]], "output": out, "hidden": True}])


def self_test(per_case):
    big = "x" * 4000
    tests_no_hidden = [dict(t, hidden=False) for t in _base()["tests"]]
    tests_no_visible = [dict(t, hidden=True) for t in _base()["tests"]]
    wrong_hidden = copy.deepcopy(_base()["tests"])
    wrong_hidden[2]["output"] = 999
    no_tags = _base()
    del no_tags["tags"]

    cases = [
        ("undefined return", _ret("let x = nums.length;", None), "strict", None),
        ("NaN return", _ret("return 0 / 0;", None), "strict", None),
        ("Infinity return", _ret("return 1 / 0;", None), "strict", None),
        ("Map return", _ret("return new Map();", {}), "strict", None),
        ("negative zero", _ret("return -0;", 0), "strict", None),
        ("wrong answer", _ret("return 0;", 2), "expected", None),
        ("thrown error", _ret("throw new Error('boom');", 0), "boom", None),
        ("infinite loop", _ret("while (true) {}", 0), "stopped before", None),
        ("wrong hidden test", _mut(tests=wrong_hidden), "hidden test #3", "999"),
        ("no hidden test", _mut(tests=tests_no_hidden), "hidden test", None),
        ("no visible test", _mut(tests=tests_no_visible), "visible test", None),
        ("bad difficulty", _mut(difficulty="extreme"), "difficulty", None),
        ("starter without solve", _mut(starter_code="function other(nums) {}"), "starter", None),
        ("bad entry_function", _mut(entry_function="foo"), "entry_function", None),
        ("oversized result", _ret("return 'x'.repeat(4000);", big), "output size", None),
        ("forbidden token", _ret("return Math.random();", 0), "forbidden", None),
        ("missing tags", no_tags, "tags", None),
    ]

    failures = 0
    good_errs, _ = validate_problem(_base(), "parts", per_case, False)
    if good_errs:
        failures += 1
        print("SELF-TEST FAIL  good fixture was rejected:", good_errs)
    else:
        print("SELF-TEST ok    good fixture accepted")

    for name, prob, needle, forbid in cases:
        errs, _ = validate_problem(prob, "parts", per_case, False)
        blob = " | ".join(errs).lower()
        if not errs or needle.lower() not in blob:
            failures += 1
            print(f"SELF-TEST FAIL  {name}: expected error containing {needle!r}, got {errs}")
        elif forbid and forbid in blob:
            failures += 1
            print(f"SELF-TEST FAIL  {name}: leaked {forbid!r} into the report")
        else:
            print(f"SELF-TEST ok    {name}")

    # production-bank schema must reject reference_solution
    errs, _, _ = validate_schema(_base(), "bank")
    if any("reference_solution" in e for e in errs):
        print("SELF-TEST ok    bank source rejects reference_solution")
    else:
        failures += 1
        print("SELF-TEST FAIL  bank source accepted reference_solution")

    # duplicate titles at bank level
    e, _, _ = check_bank([("a", _base()), ("b", _base())], 2, False, [])
    if any("duplicate title" in x for x in e):
        print("SELF-TEST ok    duplicate titles")
    else:
        failures += 1
        print("SELF-TEST FAIL  duplicate titles not detected")

    print(f"\nSelf-test: {failures} failure(s).")
    return failures


# ---------------------------------------------------------------- main

def load_entries(source, partial, top_errs):
    entries = []
    if source == "bank":
        if not BANK_PATH.exists():
            print(f"ERROR: bank not found: {BANK_PATH}")
            sys.exit(2)
        try:
            data = load_json(BANK_PATH)
        except Exception as exc:
            top_errs.append(f"javascript.json is not valid JSON: {exc}")
            return entries
        if not isinstance(data, list):
            top_errs.append("javascript.json must contain a JSON array")
            return entries
        for i, p in enumerate(data, 1):
            entries.append((f"bank#{i}", p))
        return entries

    for name in PART_NAMES:
        path = PARTS_DIR / name
        if not path.exists():
            if not partial:
                top_errs.append(f"missing part file: {path}")
            continue
        try:
            data = load_json(path)
        except Exception as exc:
            top_errs.append(f"{name} is not valid JSON: {exc}")
            continue
        if not isinstance(data, list):
            top_errs.append(f"{name} must contain a JSON array")
            continue
        if not partial and len(data) != PER_PART:
            top_errs.append(f"{name} has {len(data)} problems, expected {PER_PART}")
        for i, p in enumerate(data, 1):
            entries.append((f"{name[:-5]}#{i}", p))
    return entries


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Validate the Orin JavaScript problem bank (read-only).")
    ap.add_argument("--source", choices=["parts", "bank"], default="parts")
    ap.add_argument("--expect", type=int, default=120)
    ap.add_argument("--partial", action="store_true",
                    help="parts mode: validate existing parts only; result is not a final pass")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--show-hidden", action="store_true",
                    help="print details of failing hidden tests (local debugging only)")
    ap.add_argument("--per-case-seconds", type=float, default=2.0)
    args = ap.parse_args(argv)

    needs_node = args.self_test or args.source == "parts"
    if needs_node and not shutil.which("node"):
        print("ERROR: Node.js was not found on PATH.")
        return 2

    try:
        if args.self_test:
            return 1 if self_test(args.per_case_seconds) else 0

        top_errs = []
        entries = load_entries(args.source, args.partial, top_errs)
        total_errs, total_warns = list(top_errs), []
        failed = 0

        if args.source == "bank":
            print("Note: production bank has no reference solutions; reference execution is skipped.\n")

        for label, p in entries:
            title = p.get("title", "<no title>") if isinstance(p, dict) else "<invalid>"
            errs, warns = validate_problem(p, args.source, args.per_case_seconds, args.show_hidden)
            if errs:
                failed += 1
                print(f"FAIL  [{label}] {title}")
                for e in errs:
                    print(f"        - {e}")
            else:
                print(f"OK    [{label}] {title}")
            for w in warns:
                print(f"        ! {w}")
            total_errs += [f"[{label}] {e}" for e in errs]
            total_warns += [f"[{label}] {w}" for w in warns]

        b_errs, b_warns, info = check_bank(
            entries, args.expect, args.partial or args.source == "bank" and args.expect != 120,
            load_python_titles())
        print("\nBank-level checks:")
        for line in info:
            print(f"  {line}")
        for e in b_errs:
            print(f"  ERROR: {e}")
        for w in b_warns:
            print(f"  warn:  {w}")
        total_errs += b_errs
        total_warns += b_warns
        for e in top_errs:
            print(f"  ERROR: {e}")

        print(f"\nProblems checked: {len(entries)} | problems with errors: {failed} | "
              f"total errors: {len(total_errs)} | warnings: {len(total_warns)}")
        if total_errs:
            print("RESULT: FAIL")
            return 1
        if args.partial:
            print("RESULT: PARTIAL PASS (not a final pass; the full 120 check has not run)")
        else:
            print("RESULT: PASS")
        return 0
    except RunnerUnavailable as exc:
        print(f"ERROR: runner unavailable: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())