"""Executor + evaluator + seed-data tests. Standard library only; uses the local subprocess runner.

Also proves every seeded problem: a correct reference solution passes ALL its tests and the untouched
starter code does not (so a typo in an expected value is caught here, not by a student).
"""
import itertools

from app.services.coding.evaluator import TestSpec, evaluate, values_equal
from app.services.coding.executor import CaseRun, RunReport, run_python
from app.services.coding.seed_data import PROBLEMS

REFERENCE = {
    "Sum of Even Numbers": "def solve(nums):\n    return sum(n for n in nums if n % 2 == 0)",
    "Reverse a String": "def solve(s):\n    return s[::-1]",
    "Valid Palindrome": "def solve(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]",
    "FizzBuzz List": ("def solve(n):\n    return ['FizzBuzz' if i % 15 == 0 else 'Fizz' if i % 3 == 0 else "
                      "'Buzz' if i % 5 == 0 else str(i) for i in range(1, n + 1)]"),
    "Two Sum": ("def solve(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n"
                "        if target - n in seen:\n            return [seen[target - n], i]\n        seen[n] = i"),
}


def _run(code, inputs, **kw):
    return run_python(code, "solve", inputs, runner="subprocess", per_case_seconds=kw.pop("limit", 1.0), **kw)


def test_good_code_and_prints_are_captured():
    r = _run("def solve(a, b):\n    print('hi')\n    return a + b", [[1, 2], [3, 4]])
    assert r.fatal is None
    assert [c.value for c in r.cases] == [3, 7] and all(c.ok for c in r.cases)
    assert r.cases[0].stdout == "hi\n"


def test_runtime_error_is_reported_per_case_with_line_number():
    r = _run("def solve(a):\n    return a[5]", [[[1]], [[1, 2, 3, 4, 5, 6]]])
    assert not r.cases[0].ok and "IndexError" in r.cases[0].error and "line 2" in r.cases[0].error
    assert r.cases[1].ok and r.cases[1].value == 6      # one bad case does not stop the others


def test_syntax_error_and_missing_function_are_fatal_with_clear_messages():
    assert "SyntaxError" in _run("def solve(:\n  pass", [[1]]).fatal
    assert "'solve' was not found" in _run("def other(a): return 1", [[1]]).fatal


def test_infinite_loop_times_out_and_later_cases_are_not_run():
    r = _run("def solve(a):\n    while True:\n        pass", [[1], [2]], limit=0.8)
    assert r.cases[0].timed_out and "Time limit" in r.cases[0].error
    assert not r.cases[1].timed_out and "Not run" in r.cases[1].error


def test_exit_input_and_unserializable_results_do_not_crash_the_runner():
    assert not _run("import sys\ndef solve(a):\n    sys.exit(0)", [[1]]).cases[0].ok
    assert "EOFError" in _run("def solve(a):\n    return input()", [[1]]).cases[0].error
    assert "JSON-friendly" in _run("def solve(a):\n    return {1, 2}", [[1]]).cases[0].error


def test_huge_output_is_capped_not_stored():
    r = _run("def solve(a):\n    print('x' * 10**7)\n    return 1", [[1]], limit=3.0)
    assert r.cases[0].ok and len(r.cases[0].stdout) <= 1000


def test_api_keys_from_the_parent_environment_are_not_visible(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "should-not-leak")
    r = _run("import os\ndef solve(a):\n    return os.environ.get('GROQ_API_KEY')", [[1]])
    assert r.cases[0].value is None


def test_values_equal_rules():
    assert values_equal(1, 1) and values_equal(2, 2.0) and values_equal(0.1 + 0.2, 0.3)
    assert not values_equal(True, 1) and not values_equal("1", 1) and not values_equal(None, 0)
    assert values_equal([1, [2, 3]], [1, [2, 3]]) and not values_equal([1, 2], [2, 1])
    assert values_equal({"a": 1}, {"a": 1}) and not values_equal({"a": 1}, {"b": 1})


def test_status_priority_timeout_then_error_then_failed_then_passed():
    tests = [TestSpec(1, [1], 2), TestSpec(2, [2], 4, True)]

    def status(*cases):
        return evaluate(tests, RunReport(cases=list(cases))).status

    assert status(CaseRun(True, 2), CaseRun(True, 4)) == "passed"
    assert status(CaseRun(True, 2), CaseRun(True, 5)) == "failed"
    assert status(CaseRun(True, 2), CaseRun(False, error="boom")) == "error"
    assert status(CaseRun(False, error="t", timed_out=True), CaseRun(False, error="n")) == "timeout"
    assert evaluate(tests, RunReport(fatal="SyntaxError: x")).status == "error"


def test_every_seeded_problem_is_solvable_and_starter_code_is_not():
    assert {p["title"] for p in PROBLEMS} == set(REFERENCE)
    for p in PROBLEMS:
        specs = [TestSpec(i, a, e, h) for i, (a, e, h) in enumerate(p["tests"])]
        inputs = [s.input_data for s in specs]
        assert any(s.is_hidden for s in specs) and any(not s.is_hidden for s in specs), p["title"]
        good = evaluate(specs, _run(REFERENCE[p["title"]], inputs))
        assert (good.status, good.passed) == ("passed", len(specs)), p["title"]
        assert evaluate(specs, _run(p["starter_code"], inputs)).status == "failed", p["title"]


def test_two_sum_tests_each_have_exactly_one_answer():
    problem = next(p for p in PROBLEMS if p["title"] == "Two Sum")
    for (nums, target), expected, _ in problem["tests"]:
        pairs = [[i, j] for i, j in itertools.combinations(range(len(nums)), 2) if nums[i] + nums[j] == target]
        assert pairs == [expected]
