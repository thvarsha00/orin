"""Turns an executor RunReport into per-test verdicts and an overall submission status.

Standard library only. Statuses match the `submissions.status` column: passed | failed | error | timeout.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

from app.services.coding.executor import RunReport

PREVIEW_CHARS = 500
FLOAT_TOL = 1e-6


@dataclass
class TestSpec:
    __test__ = False   # not a pytest class
    id: int
    input_data: list
    expected_output: object
    is_hidden: bool = False


@dataclass
class Verdict:
    test_id: int
    hidden: bool
    passed: bool
    actual: str | None = None      # JSON preview of what the code returned
    error: str | None = None
    time_ms: float = 0.0
    timed_out: bool = False
    stdout: str = ""


@dataclass
class Evaluation:
    status: str
    passed: int
    total: int
    total_time_s: float
    verdicts: list[Verdict]
    error: str | None = None       # code could not be loaded (syntax error, wrong function name)


def values_equal(actual: object, expected: object) -> bool:
    """Strict on types (True is not 1), tolerant on float rounding, recursive for lists and dicts."""
    if isinstance(actual, bool) or isinstance(expected, bool):
        return isinstance(actual, bool) and isinstance(expected, bool) and actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        if isinstance(actual, float) or isinstance(expected, float):
            return math.isclose(actual, expected, rel_tol=FLOAT_TOL, abs_tol=FLOAT_TOL)
        return actual == expected
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(values_equal(a, e) for a, e in zip(actual, expected))
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(values_equal(actual[k], expected[k]) for k in expected)
    return type(actual) is type(expected) and actual == expected


def preview(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= PREVIEW_CHARS else text[:PREVIEW_CHARS] + "..."


def evaluate(tests: list[TestSpec], report: RunReport) -> Evaluation:
    if report.fatal:
        verdicts = [Verdict(t.id, t.is_hidden, False, error=report.fatal) for t in tests]
        return Evaluation("error", 0, len(tests), 0.0, verdicts, error=report.fatal)

    verdicts: list[Verdict] = []
    for test, run in zip(tests, report.cases):
        if run.ok:
            ok = values_equal(run.value, test.expected_output)
            verdicts.append(Verdict(test.id, test.is_hidden, ok, actual=preview(run.value),
                                    time_ms=run.time_ms, stdout=run.stdout))
        else:
            verdicts.append(Verdict(test.id, test.is_hidden, False, error=run.error, time_ms=run.time_ms,
                                    timed_out=run.timed_out, stdout=run.stdout))

    passed = sum(v.passed for v in verdicts)
    if any(v.timed_out for v in verdicts):
        status = "timeout"
    elif any(v.error for v in verdicts):
        status = "error"
    elif passed < len(verdicts):
        status = "failed"
    else:
        status = "passed"
    total_time = sum(v.time_ms for v in verdicts) / 1000
    return Evaluation(status, passed, len(verdicts), total_time, verdicts)
