"""
Validate a batch of problems by running each reference solution against
its own tests, then append passing problems to problem_bank/<lang>.json.

Usage (from backend/):
    python .\tools\merge_batch.py .\tools\batches\python_batch01.json
    python .\tools\merge_batch.py .\tools\batches\python_batch01.json --dry-run

Python problems only for now (reference solutions are executed with exec()).
This runs YOUR OWN batch files locally. Do not run batch files you don't trust.
"""
import copy
import json
import shutil
import sys
from pathlib import Path

BANK_DIR = Path(__file__).resolve().parent.parent / "app" / "services" / "coding" / "problem_bank"
REQUIRED = ["title", "topic", "difficulty", "description", "examples",
            "constraints", "starter_code", "entry_function", "tests"]
DIFFICULTIES = {"easy", "medium", "hard"}


def load_bank(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data, data
    if isinstance(data, dict) and isinstance(data.get("problems"), list):
        return data, data["problems"]
    raise SystemExit("Unrecognized bank format. Expected a list or {'problems': [...]}.")


def check_problem(p):
    errors = []
    for k in REQUIRED:
        if k not in p:
            errors.append(f"missing key '{k}'")
    if errors:
        return errors
    if p["difficulty"] not in DIFFICULTIES:
        errors.append(f"bad difficulty '{p['difficulty']}'")
    if f"def {p['entry_function']}(" not in p["starter_code"]:
        errors.append("starter_code does not define entry_function")
    tests = p["tests"]
    if not any(not t.get("hidden") for t in tests):
        errors.append("needs at least 1 visible test")
    if not any(t.get("hidden") for t in tests):
        errors.append("needs at least 1 hidden test")
    for i, t in enumerate(tests):
        if not isinstance(t.get("input"), list):
            errors.append(f"test {i}: 'input' must be a list of arguments")
        if "output" not in t or not isinstance(t.get("hidden"), bool):
            errors.append(f"test {i}: needs 'output' and boolean 'hidden'")
    if "reference_solution" not in p:
        errors.append("missing reference_solution")
    return errors


def run_reference(p):
    errors = []
    ns = {}
    try:
        exec(p["reference_solution"], ns)
        fn = ns[p["entry_function"]]
    except Exception as e:
        return [f"reference solution failed to load: {e!r}"]
    for i, t in enumerate(p["tests"]):
        try:
            result = fn(*copy.deepcopy(t["input"]))
            result = json.loads(json.dumps(result))
        except Exception as e:
            errors.append(f"test {i}: raised {e!r}")
            continue
        if result != t["output"]:
            errors.append(f"test {i}: expected {t['output']!r}, reference gave {result!r}")
    return errors


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    batch_path = Path(args[0])
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    if not isinstance(batch, list):
        raise SystemExit("Batch file must be a JSON list of problems.")

    bank_path = BANK_DIR / "python.json"
    container, problems = load_bank(bank_path)
    existing = {p["title"].strip().lower() for p in problems}

    to_add, failed, skipped = [], 0, 0
    seen = set()
    for p in batch:
        title = p.get("title", "<no title>")
        key = title.strip().lower()
        if key in existing or key in seen:
            print(f"SKIP  {title} (duplicate title)")
            skipped += 1
            continue
        errs = check_problem(p) or run_reference(p)
        if errs:
            failed += 1
            print(f"FAIL  {title}")
            for e in errs:
                print(f"        - {e}")
            continue
        seen.add(key)
        clean = {k: v for k, v in p.items() if k != "reference_solution"}
        to_add.append(clean)
        print(f"OK    {title}  ({p['difficulty']}, {len(p['tests'])} tests)")

    print(f"\n{len(to_add)} ok, {failed} failed, {skipped} skipped.")
    if failed:
        print("Fix the failures and re-run. Nothing was written.")
        raise SystemExit(1)
    if dry or not to_add:
        print("Dry run / nothing to add. Nothing was written.")
        return

    shutil.copyfile(bank_path, bank_path.with_suffix(".json.bak"))
    problems.extend(to_add)
    bank_path.write_text(json.dumps(container, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Appended {len(to_add)} problems. Backup: {bank_path.with_suffix('.json.bak').name}")
    print(f"python.json now has {len(problems)} problems.")


if __name__ == "__main__":
    main()