from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field


MARK = "@@ORIN@@"

MAX_OUTPUT_CHARS = 4000


class RunnerUnavailable(Exception):
    """The selected local runtime is unavailable."""


@dataclass
class CaseRun:
    ok: bool
    value: object = None
    error: str | None = None
    time_ms: float = 0.0
    stdout: str = ""
    timed_out: bool = False


@dataclass
class RunReport:
    cases: list[CaseRun] = field(default_factory=list)
    fatal: str | None = None


def _safe_error(text: str, limit: int = 1000) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def _parse_result_line(line: str):
    if not line.startswith(MARK):
        return None

    try:
        return json.loads(line[len(MARK):])
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

PYTHON_HARNESS = r'''
import io
import json
import sys
import time
import traceback

MARK = "@@ORIN@@"
real_out = sys.stdout


def emit(obj):
    real_out.write(MARK + json.dumps(obj) + "\n")
    real_out.flush()


def short(text, n=2000):
    text = str(text)
    return text if len(text) <= n else text[:n] + "...[truncated]"


class Cap:
    def __init__(self):
        self.s = ""

    def write(self, t):
        if len(self.s) < 1000:
            self.s += str(t)[:1000 - len(self.s)]
        return len(str(t))

    def flush(self):
        pass

    def getvalue(self):
        return self.s


def describe(e):
    if isinstance(e, SyntaxError):
        return "SyntaxError: %s (line %s)" % (e.msg, e.lineno)

    line = None

    try:
        for fr in traceback.extract_tb(e.__traceback__):
            if fr.filename == "solution.py":
                line = fr.lineno
    except Exception:
        pass

    msg = "%s: %s" % (type(e).__name__, e)

    if line:
        msg += " (line %s)" % line

    return short(msg)


def main():
    payload = json.loads(sys.stdin.read())

    sys.stdin = io.StringIO("")

    ns = {
        "__name__": "__orin_solution__"
    }

    cap = Cap()
    sys.stdout = cap

    try:
        exec(
            compile(payload["code"], "solution.py", "exec"),
            ns
        )
    except BaseException as e:
        sys.stdout = real_out
        emit({
            "fatal": describe(e)
        })
        return

    sys.stdout = real_out

    fn = ns.get(payload["entry"])

    if not callable(fn):
        emit({
            "fatal":
                "Function '%s' was not found. Define it with exactly that name, "
                "as in the starter code."
                % payload["entry"]
        })
        return

    for i, args in enumerate(payload["inputs"]):
        cap = Cap()
        sys.stdout = cap

        t0 = time.perf_counter()

        try:
            value = fn(*args)

            ms = (time.perf_counter() - t0) * 1000

            sys.stdout = real_out

            try:
                json.dumps(value)
            except (TypeError, ValueError):
                emit({
                    "i": i,
                    "ok": False,
                    "ms": ms,
                    "stdout": cap.getvalue(),
                    "error":
                        "Return a JSON-friendly value "
                        "(numbers, strings, booleans, lists, dicts). "
                        "Got %s." % type(value).__name__
                })
                continue

            emit({
                "i": i,
                "ok": True,
                "value": value,
                "ms": ms,
                "stdout": cap.getvalue()
            })

        except BaseException as e:
            sys.stdout = real_out

            emit({
                "i": i,
                "ok": False,
                "ms": (time.perf_counter() - t0) * 1000,
                "stdout": cap.getvalue(),
                "error": describe(e)
            })


main()
'''


# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------

JAVASCRIPT_HARNESS = r'''
const fs = require("fs");

const MARK = "@@ORIN@@";

function emit(obj) {
    process.stdout.write(MARK + JSON.stringify(obj) + "\n");
}

function short(text, n = 2000) {
    text = String(text ?? "");

    if (text.length <= n) {
        return text;
    }

    return text.slice(0, n) + "...[truncated]";
}

function normalize(value) {
    if (
        value === null ||
        typeof value === "number" ||
        typeof value === "string" ||
        typeof value === "boolean"
    ) {
        return value;
    }

    if (Array.isArray(value)) {
        return value.map(normalize);
    }

    if (typeof value === "object") {
        const result = {};

        for (const [key, val] of Object.entries(value)) {
            result[key] = normalize(val);
        }

        return result;
    }

    throw new Error(
        "Return a JSON-friendly value."
    );
}

function main() {
    let payload;

    try {
        payload = JSON.parse(fs.readFileSync(0, "utf8"));
    } catch (error) {
        emit({
            fatal: "Invalid runner input."
        });
        return;
    }

    let solve;

    try {
        const wrapped = new Function(
            "require",
            "process",
            payload.code +
            "\nreturn typeof " +
            payload.entry +
            " === 'function' ? " +
            payload.entry +
            " : null;"
        );

        solve = wrapped(require, process);

    } catch (error) {
        emit({
            fatal:
                error.name +
                ": " +
                short(error.message)
        });
        return;
    }

    if (typeof solve !== "function") {
        emit({
            fatal:
                "Function '" +
                payload.entry +
                "' was not found. Define it with exactly that name."
        });
        return;
    }

    for (let i = 0; i < payload.inputs.length; i++) {
        const args = payload.inputs[i];

        const start = process.hrtime.bigint();

        let stdout = "";

        const originalLog = console.log;

        console.log = (...items) => {
            if (stdout.length < 1000) {
                stdout += items.join(" ") + "\n";
                stdout = stdout.slice(0, 1000);
            }
        };

        try {
            const value = solve(...args);

            const end = process.hrtime.bigint();

            console.log = originalLog;

            const normalized = normalize(value);

            emit({
                i: i,
                ok: true,
                value: normalized,
                ms: Number(end - start) / 1000000,
                stdout: stdout
            });

        } catch (error) {
            const end = process.hrtime.bigint();

            console.log = originalLog;

            emit({
                i: i,
                ok: false,
                ms: Number(end - start) / 1000000,
                stdout: stdout,
                error:
                    error.name +
                    ": " +
                    short(error.message)
            });
        }
    }
}

main();
'''


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

JAVA_RUNNER = r'''
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import javax.tools.*;

public class OrinRunner {

    static final String MARK = "@@ORIN@@";

    static void emit(String json) {
        System.out.println(MARK + json);
        System.out.flush();
    }

    static String readAll() throws Exception {
        return new String(
            System.in.readAllBytes(),
            StandardCharsets.UTF_8
        );
    }

    static String escape(String value) {
        if (value == null) {
            return "";
        }

        return value
            .replace("\\", "\\\\")
            .replace("\"", "\\\"")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\t", "\\t");
    }

    public static void main(String[] args) {

        try {
            String source = readAll();

            /*
             * The Java adapter currently expects the user's submitted code
             * to contain a public class named Main with:
             *
             * public static Object solve(...)
             *
             * Java problems will be added with Java-specific starter code.
             *
             * This runner is intentionally kept separate from the Python
             * function runner.
             */

            emit(
                "{\"fatal\":\"Java execution adapter is installed, but Java problem harness support will be enabled with Java-specific problems.\"}"
            );

        } catch (Exception e) {
            emit(
                "{\"fatal\":\"Java runner error: " +
                escape(e.getMessage()) +
                "\"}"
            );
        }
    }
}
'''


# ---------------------------------------------------------------------------
# Generic local process runner
# ---------------------------------------------------------------------------

def _run_process(
    command: list[str],
    payload: str,
    *,
    timeout_seconds: float,
    cwd: str,
) -> RunReport:

    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=_safe_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        raise RunnerUnavailable(
            f"Could not start the runtime: {exc}"
        ) from exc

    stdout_lines: list[str] = []
    stderr_text: list[str] = []

    try:
        stdout, stderr = proc.communicate(
            payload,
            timeout=timeout_seconds,
        )

    except subprocess.TimeoutExpired:
        proc.kill()

        try:
            stdout, stderr = proc.communicate(timeout=2)
        except Exception:
            stdout, stderr = "", ""

        return RunReport(
            cases=[
                CaseRun(
                    ok=False,
                    timed_out=True,
                    error=(
                        f"Time limit exceeded "
                        f"({timeout_seconds:g}s)."
                    ),
                )
            ]
        )

    if stdout:
        stdout_lines = stdout.splitlines()

    if stderr:
        stderr_text.append(stderr[:MAX_OUTPUT_CHARS])

    parsed = []

    for line in stdout_lines:
        result = _parse_result_line(line)

        if result is not None:
            parsed.append(result)

    if parsed and "fatal" in parsed[0]:
        return RunReport(
            fatal=_safe_error(parsed[0]["fatal"])
        )

    if not parsed:
        error = "\n".join(stderr_text).strip()

        if not error:
            error = (
                "The program stopped without returning a result."
            )

        return RunReport(
            fatal=_safe_error(error)
        )

    cases: list[CaseRun] = []

    for item in parsed:
        if "i" not in item:
            continue

        cases.append(
            CaseRun(
                ok=bool(item.get("ok")),
                value=item.get("value"),
                error=item.get("error"),
                time_ms=float(item.get("ms", 0)),
                stdout=str(item.get("stdout", ""))[:1000],
                timed_out=bool(item.get("timed_out", False)),
            )
        )

    return RunReport(cases=cases)


def _safe_env() -> dict[str, str]:

    allowed = (
        "SYSTEMROOT",
        "SYSTEMDRIVE",
        "TEMP",
        "TMP",
        "PATH",
        "LANG",
        "LC_ALL",
    )

    env = {
        key: os.environ[key]
        for key in allowed
        if key in os.environ
    }

    env["PYTHONIOENCODING"] = "utf-8"

    return env


# ---------------------------------------------------------------------------
# Python runner
# ---------------------------------------------------------------------------

def run_python(
    code: str,
    entry: str,
    inputs: list[list],
    *,
    runner: str = "subprocess",
    per_case_seconds: float = 2.0,
    docker_image: str = "python:3.12-slim",
    memory_mb: int = 128,
) -> RunReport:

    if runner == "docker":
        raise RunnerUnavailable(
            "Docker execution is not available in this development setup. "
            "Use the explicitly enabled local runner."
        )

    if runner != "subprocess":
        raise RunnerUnavailable(
            f"Unknown Python runner '{runner}'."
        )

    payload = json.dumps({
        "code": code,
        "entry": entry,
        "inputs": inputs,
    })

    # Preserve the existing isolated Python behavior.
    command = [
        sys.executable,
        "-I",
        "-c",
        "import base64,sys;exec(base64.b64decode(sys.argv[1]).decode())",
        __import__("base64").b64encode(
            PYTHON_HARNESS.encode()
        ).decode(),
    ]

    with tempfile.TemporaryDirectory(
        prefix="orin_python_"
    ) as workdir:

        return _run_process(
            command,
            payload,
            timeout_seconds=max(
                4.0,
                per_case_seconds * max(1, len(inputs)) + 2.0
            ),
            cwd=workdir,
        )


# ---------------------------------------------------------------------------
# JavaScript runner
# ---------------------------------------------------------------------------

def run_javascript(
    code: str,
    entry: str,
    inputs: list[list],
    *,
    per_case_seconds: float = 2.0,
) -> RunReport:

    if not shutil.which("node"):
        raise RunnerUnavailable(
            "Node.js was not found. Install Node.js and restart the terminal."
        )

    payload = json.dumps({
        "code": code,
        "entry": entry,
        "inputs": inputs,
    })

    bootstrap = (
        "const fs=require('fs');"
        "const vm=require('vm');"
        "const payload=JSON.parse(fs.readFileSync(0,'utf8'));"
        "eval(payload.code);"
        "const result=typeof payload.entry;"
    )

    # We use the standalone harness file so the student's program
    # receives exactly the same JSON protocol as Python.
    with tempfile.TemporaryDirectory(
        prefix="orin_js_"
    ) as workdir:

        harness_path = os.path.join(
            workdir,
            "runner.js"
        )

        with open(
            harness_path,
            "w",
            encoding="utf-8"
        ) as f:
            f.write(JAVASCRIPT_HARNESS)

        return _run_process(
            ["node", harness_path],
            payload,
            timeout_seconds=max(
                4.0,
                per_case_seconds * max(1, len(inputs)) + 2.0
            ),
            cwd=workdir,
        )


# ---------------------------------------------------------------------------
# Java adapter
# ---------------------------------------------------------------------------

def run_java(
    code: str,
    entry: str,
    inputs: list[list],
    *,
    per_case_seconds: float = 2.0,
) -> RunReport:

    if not shutil.which("java"):
        raise RunnerUnavailable(
            "Java runtime was not found."
        )

    if not shutil.which("javac"):
        raise RunnerUnavailable(
            "Java compiler (javac) was not found."
        )

    return RunReport(
        fatal=(
            "Java runtime is detected, but Java coding problems "
            "have not been enabled yet."
        )
    )


# ---------------------------------------------------------------------------
# Multi-language dispatcher
# ---------------------------------------------------------------------------

def run_code(
    language: str,
    code: str,
    entry: str,
    inputs: list[list],
    *,
    runner: str = "subprocess",
    per_case_seconds: float = 2.0,
    docker_image: str = "python:3.12-slim",
    memory_mb: int = 128,
) -> RunReport:

    language = language.strip().lower()

    if language == "python":
        return run_python(
            code,
            entry,
            inputs,
            runner=runner,
            per_case_seconds=per_case_seconds,
            docker_image=docker_image,
            memory_mb=memory_mb,
        )

    if language in ("javascript", "js"):
        return run_javascript(
            code,
            entry,
            inputs,
            per_case_seconds=per_case_seconds,
        )

    if language == "java":
        return run_java(
            code,
            entry,
            inputs,
            per_case_seconds=per_case_seconds,
        )

    raise RunnerUnavailable(
        f"Language '{language}' is not supported yet."
    )