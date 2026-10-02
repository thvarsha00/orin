"""Orin Code execution service.

Supports:
- Docker execution for production / untrusted code
- Explicitly enabled local subprocess execution for private development
- Python
- JavaScript
- Java runtime detection

The local subprocess runner is NOT a secure sandbox.
Docker remains the recommended production execution environment.
"""

from __future__ import annotations

import base64
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
    """The selected runner cannot execute code right now."""


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


# ---------------------------------------------------------------------------
# Python harness
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

    def write(self, text):
        if len(self.s) < 1000:
            self.s += text[:1000 - len(self.s)]
        return len(text)

    def flush(self):
        pass

    def getvalue(self):
        return self.s


def describe(exc):
    if isinstance(exc, SyntaxError):
        return "SyntaxError: %s (line %s)" % (
            exc.msg,
            exc.lineno,
        )

    line = None

    try:
        for frame in traceback.extract_tb(exc.__traceback__):
            if frame.filename == "solution.py":
                line = frame.lineno
    except Exception:
        pass

    message = "%s: %s" % (
        type(exc).__name__,
        exc,
    )

    if line:
        message += " (line %s)" % line

    return short(message)


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except Exception as exc:
        emit({
            "fatal": "Invalid execution payload: %s" % exc
        })
        return

    sys.stdin = io.StringIO("")

    namespace = {
        "__name__": "__orin_solution__"
    }

    try:
        exec(
            compile(
                payload["code"],
                "solution.py",
                "exec",
            ),
            namespace,
        )
    except BaseException as exc:
        sys.stdout = real_out
        emit({
            "fatal": describe(exc)
        })
        return

    sys.stdout = real_out

    entry = payload["entry"]
    function = namespace.get(entry)

    if not callable(function):
        emit({
            "fatal": (
                "Function '%s' was not found. "
                "Define it with exactly that name."
            ) % entry
        })
        return

    for index, args in enumerate(payload["inputs"]):
        captured = Cap()
        sys.stdout = captured

        start = time.perf_counter()

        try:
            value = function(*args)

            elapsed_ms = (
                time.perf_counter() - start
            ) * 1000

            sys.stdout = real_out

            try:
                json.dumps(value)
            except (TypeError, ValueError):
                emit({
                    "i": index,
                    "ok": False,
                    "ms": elapsed_ms,
                    "stdout": captured.getvalue(),
                    "error": (
                        "Return a JSON-friendly value "
                        "(numbers, strings, booleans, lists, dicts); "
                        "got %s."
                    ) % type(value).__name__,
                })
                continue

            emit({
                "i": index,
                "ok": True,
                "value": value,
                "ms": elapsed_ms,
                "stdout": captured.getvalue(),
            })

        except BaseException as exc:
            sys.stdout = real_out

            emit({
                "i": index,
                "ok": False,
                "ms": (
                    time.perf_counter() - start
                ) * 1000,
                "stdout": captured.getvalue(),
                "error": describe(exc),
            })


main()
'''


# ---------------------------------------------------------------------------
# JavaScript harness
# ---------------------------------------------------------------------------

JAVASCRIPT_HARNESS = r'''
const fs = require("fs");

const MARK = "@@ORIN@@";

function emit(obj) {
    process.stdout.write(
        MARK + JSON.stringify(obj) + "\n"
    );
}

function short(text, n = 2000) {
    text = String(text);

    if (text.length <= n) {
        return text;
    }

    return text.slice(0, n) + "...[truncated]";
}

function normalize(value) {
    JSON.stringify(value);
    return value;
}

let payload;

try {
    payload = JSON.parse(
        fs.readFileSync(0, "utf8")
    );
} catch (err) {
    emit({
        fatal: "Invalid execution payload: " + err.message
    });

    process.exit(0);
}

let solution;

try {
    const moduleFactory = new Function(
        "require",
        "process",
        payload.code +
        "\n; return typeof " +
        payload.entry +
        " === 'function' ? " +
        payload.entry +
        " : null;"
    );

    solution = moduleFactory(
        require,
        process
    );
} catch (err) {
    emit({
        fatal: short(
            err.name + ": " + err.message
        )
    });

    process.exit(0);
}

if (typeof solution !== "function") {
    emit({
        fatal:
            "Function '" +
            payload.entry +
            "' was not found. " +
            "Define it with exactly that name."
    });

    process.exit(0);
}

for (
    let index = 0;
    index < payload.inputs.length;
    index++
) {
    const args = payload.inputs[index];

    let output = "";
    const originalLog = console.log;

    console.log = (...items) => {
        if (output.length < 1000) {
            output += items.join(" ") + "\n";
        }
    };

    const start = process.hrtime.bigint();

    try {
        const value = solution(...args);

        const elapsedMs =
            Number(
                process.hrtime.bigint() - start
            ) / 1000000;

        console.log = originalLog;

        try {
            normalize(value);
        } catch (err) {
            emit({
                i: index,
                ok: false,
                ms: elapsedMs,
                stdout: output,
                error:
                    "Return a JSON-friendly value."
            });

            continue;
        }

        emit({
            i: index,
            ok: true,
            value: value,
            ms: elapsedMs,
            stdout: output
        });

    } catch (err) {
        const elapsedMs =
            Number(
                process.hrtime.bigint() - start
            ) / 1000000;

        console.log = originalLog;

        emit({
            i: index,
            ok: false,
            ms: elapsedMs,
            stdout: output,
            error: short(
                err.name + ": " + err.message
            )
        });
    }
}
'''


# ---------------------------------------------------------------------------
# Shared runner configuration
# ---------------------------------------------------------------------------

_ENV_ALLOW = (
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "TEMP",
    "TMP",
    "LANG",
    "LC_ALL",
    "PATH",
)


def _child_env() -> dict[str, str]:
    """Return a deliberately reduced environment for local execution."""

    env = {
        key: os.environ[key]
        for key in _ENV_ALLOW
        if key in os.environ
    }

    env["PYTHONIOENCODING"] = "utf-8"

    return env


def _safe_text(value: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    value = str(value)

    if len(value) <= limit:
        return value

    return value[:limit] + "...[truncated]"


# ---------------------------------------------------------------------------
# Process runner
# ---------------------------------------------------------------------------

def _run_process(
    *,
    command: list[str],
    payload: bytes,
    runner: str,
    container_name: str | None,
    per_case_seconds: float,
    startup_seconds: float,
    env: dict[str, str] | None,
) -> RunReport:

    lines: list[str] = []
    stderr_parts: list[str] = []

    lock = threading.Lock()

    with tempfile.TemporaryDirectory(
        prefix="orin_run_"
    ) as workdir:

        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=workdir,
                env=env,
            )

        except OSError as exc:
            raise RunnerUnavailable(
                "Could not start the code runner "
                f"({exc.__class__.__name__})."
            ) from exc

        def read_stdout():
            if process.stdout is None:
                return

            for raw in process.stdout:
                text = raw.decode(
                    "utf-8",
                    "replace",
                ).rstrip("\n")

                if not text.startswith(MARK):
                    continue

                data = text[len(MARK):]

                with lock:
                    if sum(len(x) for x in lines) < MAX_OUTPUT_CHARS:
                        lines.append(data)

        def read_stderr():
            if process.stderr is None:
                return

            total = 0

            for raw in process.stderr:
                if total >= MAX_OUTPUT_CHARS:
                    break

                chunk = raw.decode(
                    "utf-8",
                    "replace",
                )

                remaining = (
                    MAX_OUTPUT_CHARS - total
                )

                stderr_parts.append(
                    chunk[:remaining]
                )

                total += len(chunk)

        stdout_thread = threading.Thread(
            target=read_stdout,
            daemon=True,
        )

        stderr_thread = threading.Thread(
            target=read_stderr,
            daemon=True,
        )

        stdout_thread.start()
        stderr_thread.start()

        def feed():
            try:
                if process.stdin is not None:
                    process.stdin.write(payload)
                    process.stdin.close()
            except OSError:
                pass

        threading.Thread(
            target=feed,
            daemon=True,
        ).start()

        timed_out = False
        seen = 0
        last_progress = time.monotonic()

        while process.poll() is None:

            with lock:
                current_count = len(lines)

            now = time.monotonic()

            if current_count != seen:
                seen = current_count
                last_progress = now

            timeout_limit = (
                startup_seconds
                if seen == 0
                else per_case_seconds
            )

            if now - last_progress > timeout_limit:
                timed_out = True

                try:
                    process.kill()
                except OSError:
                    pass

                if (
                    runner == "docker"
                    and container_name
                ):
                    try:
                        subprocess.run(
                            [
                                "docker",
                                "kill",
                                container_name,
                            ],
                            capture_output=True,
                            timeout=10,
                        )
                    except Exception:
                        pass

                break

            time.sleep(0.02)

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass

            process.wait()

        stdout_thread.join(timeout=2)
        stderr_thread.join(timeout=2)

        return_code = process.returncode

    stderr = "".join(stderr_parts)

    if (
        runner == "docker"
        and not lines
        and not timed_out
        and (
            return_code in (125, 126, 127)
            or "daemon" in stderr.lower()
            or "docker" in stderr.lower()
        )
    ):
        raise RunnerUnavailable(
            "Docker is installed but could not run the code. "
            "Make sure Docker Desktop is running."
        )

    parsed: list[dict] = []

    for line in lines:
        try:
            parsed.append(
                json.loads(line)
            )
        except json.JSONDecodeError:
            continue

    if (
        parsed
        and "fatal" in parsed[0]
    ):
        return RunReport(
            fatal=parsed[0]["fatal"]
        )

    by_index = {
        item["i"]: item
        for item in parsed
        if "i" in item
    }

    return RunReport(
        cases=_build_cases(
            by_index=by_index,
            input_count=None,
            timed_out=timed_out,
            per_case_seconds=per_case_seconds,
        )
    )


def _build_cases(
    *,
    by_index: dict[int, dict],
    input_count: int | None,
    timed_out: bool,
    per_case_seconds: float,
) -> list[CaseRun]:

    if input_count is None:
        input_count = (
            max(by_index.keys()) + 1
            if by_index
            else 0
        )

    cases: list[CaseRun] = []

    for index in range(input_count):

        result = by_index.get(index)

        if result:
            cases.append(
                CaseRun(
                    ok=bool(
                        result.get(
                            "ok",
                            False,
                        )
                    ),
                    value=result.get(
                        "value"
                    ),
                    error=result.get(
                        "error"
                    ),
                    time_ms=float(
                        result.get(
                            "ms",
                            0.0,
                        )
                    ),
                    stdout=_safe_text(
                        result.get(
                            "stdout",
                            "",
                        )
                    ),
                )
            )

        elif timed_out:
            cases.append(
                CaseRun(
                    ok=False,
                    timed_out=True,
                    error=(
                        "Time limit exceeded "
                        f"({per_case_seconds:g}s). "
                        "Check for an infinite loop "
                        "or a slow approach."
                    ),
                )
            )

        else:
            cases.append(
                CaseRun(
                    ok=False,
                    error=(
                        "The program stopped unexpectedly "
                        "before this test ran."
                    ),
                )
            )

    return cases


# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------

def _python_command(
    *,
    runner: str,
    docker_image: str,
    memory_mb: int,
    container_name: str,
) -> list[str]:

    harness_b64 = base64.b64encode(
        PYTHON_HARNESS.encode()
    ).decode()

    boot = (
        "import base64,sys;"
        "exec(base64.b64decode(sys.argv[1]).decode())"
    )

    if runner == "subprocess":
        return [
            sys.executable,
            "-I",
            "-c",
            boot,
            harness_b64,
        ]

    if runner == "docker":

        if not shutil.which("docker"):
            raise RunnerUnavailable(
                "Docker was not found. "
                "For private local development, "
                "set CODE_RUNNER=subprocess and "
                "CODE_ALLOW_UNSAFE_LOCAL=1."
            )

        return [
            "docker",
            "run",
            "--rm",
            "-i",
            "--name",
            container_name,
            "--network",
            "none",
            "--memory",
            f"{memory_mb}m",
            "--memory-swap",
            f"{memory_mb}m",
            "--cpus",
            "0.5",
            "--pids-limit",
            "64",
            "--read-only",
            "--tmpfs",
            "/tmp:size=16m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            "65534:65534",
            docker_image,
            "python",
            "-I",
            "-c",
            boot,
            harness_b64,
        ]

    raise RunnerUnavailable(
        f"Unknown CODE_RUNNER '{runner}'. "
        "Use docker or subprocess."
    )


def _javascript_command() -> list[str]:
    node = shutil.which("node")

    if not node:
        raise RunnerUnavailable(
            "Node.js was not found. "
            "Install Node.js or disable JavaScript problems."
        )

    return [
        node,
        "-e",
        JAVASCRIPT_HARNESS,
    ]


# ---------------------------------------------------------------------------
# Python execution
# ---------------------------------------------------------------------------

def run_python(
    code: str,
    entry: str,
    inputs: list[list],
    *,
    runner: str = "docker",
    per_case_seconds: float = 2.0,
    docker_image: str = "python:3.12-slim",
    memory_mb: int = 128,
) -> RunReport:

    container_name = (
        f"orin-run-{uuid.uuid4().hex[:12]}"
    )

    command = _python_command(
        runner=runner,
        docker_image=docker_image,
        memory_mb=memory_mb,
        container_name=container_name,
    )

    payload = json.dumps(
        {
            "code": code,
            "entry": entry,
            "inputs": inputs,
        }
    ).encode()

    report = _run_process(
        command=command,
        payload=payload,
        runner=runner,
        container_name=container_name,
        per_case_seconds=per_case_seconds,
        startup_seconds=25.0
        if runner == "docker"
        else 4.0,
        env=(
            _child_env()
            if runner == "subprocess"
            else None
        ),
    )

    if report.fatal:
        return report

    if len(report.cases) < len(inputs):
        report.cases.extend(
            _build_cases(
                by_index={
                    i: {
                        "ok": False,
                        "error": (
                            "The program stopped "
                            "before this test ran."
                        ),
                    }
                    for i in range(
                        len(report.cases),
                        len(inputs),
                    )
                },
                input_count=len(inputs),
                timed_out=False,
                per_case_seconds=per_case_seconds,
            )
        )

    return report


# ---------------------------------------------------------------------------
# JavaScript execution
# ---------------------------------------------------------------------------

def run_javascript(
    code: str,
    entry: str,
    inputs: list[list],
    *,
    runner: str = "subprocess",
    per_case_seconds: float = 2.0,
    memory_mb: int = 128,
) -> RunReport:

    if runner == "docker":
        raise RunnerUnavailable(
            "JavaScript Docker execution is not enabled yet. "
            "Use local subprocess execution only for trusted "
            "development."
        )

    if runner != "subprocess":
        raise RunnerUnavailable(
            f"Unsupported JavaScript runner '{runner}'."
        )

    command = _javascript_command()

    payload = json.dumps(
        {
            "code": code,
            "entry": entry,
            "inputs": inputs,
        }
    ).encode()

    report = _run_process(
        command=command,
        payload=payload,
        runner="subprocess",
        container_name=None,
        per_case_seconds=per_case_seconds,
        startup_seconds=4.0,
        env=_child_env(),
    )

    if report.fatal:
        return report

    if len(report.cases) < len(inputs):
        missing = len(inputs) - len(
            report.cases
        )

        report.cases.extend(
            CaseRun(
                ok=False,
                error=(
                    "The program stopped "
                    "before this test ran."
                ),
            )
            for _ in range(missing)
        )

    return report


# ---------------------------------------------------------------------------
# Java
# ---------------------------------------------------------------------------

def run_java(
    code: str,
    entry: str,
    inputs: list[list],
    *,
    runner: str = "subprocess",
    per_case_seconds: float = 2.0,
    memory_mb: int = 128,
) -> RunReport:

    java = shutil.which("java")
    javac = shutil.which("javac")

    if not java or not javac:
        raise RunnerUnavailable(
            "Java requires both 'java' and 'javac'. "
            "A JDK installation is required."
        )

    raise RunnerUnavailable(
        "Java runtime and javac were detected, "
        "but Java coding problems are not enabled yet. "
        "The Java execution adapter will be added before "
        "Java problems are seeded."
    )


# ---------------------------------------------------------------------------
# Public dispatcher
# ---------------------------------------------------------------------------

def run_code(
    *,
    language: str,
    code: str,
    entry: str,
    inputs: list[list],
    runner: str = "docker",
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

    if language in {
        "javascript",
        "js",
    }:
        return run_javascript(
            code,
            entry,
            inputs,
            runner=runner,
            per_case_seconds=per_case_seconds,
            memory_mb=memory_mb,
        )

    if language == "java":
        return run_java(
            code,
            entry,
            inputs,
            runner=runner,
            per_case_seconds=per_case_seconds,
            memory_mb=memory_mb,
        )

    raise RunnerUnavailable(
        f"Language '{language}' is not supported yet."
    )