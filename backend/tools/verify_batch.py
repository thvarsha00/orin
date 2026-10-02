import json
import sqlite3
import sys
from pathlib import Path

BATCH = Path(sys.argv[1] if len(sys.argv) > 1 else "tools/batches/python_batch05.json")
titles = [p["title"] for p in json.loads(BATCH.read_text(encoding="utf-8"))]

c = sqlite3.connect("file:orin.db?mode=ro", uri=True)

dups = c.execute(
    "select title, language, count(*) from coding_problems "
    "group by title, language having count(*) > 1"
).fetchall()
print("Duplicate groups:", len(dups))
for d in dups:
    print("  ", d)

print()
print("Problems per language:")
for lang, n in c.execute(
    "select language, count(*) from coding_problems group by language order by language"
):
    print("  ", lang, n)

print()
print(f"Batch check ({BATCH.name}):")
bad = 0
total_tests = 0
for t in titles:
    row = c.execute(
        "select id, tags, hints from coding_problems where title = ? and language = 'python'",
        (t,),
    ).fetchall()
    if len(row) != 1:
        print(f"  PROBLEM: '{t}' found {len(row)} times")
        bad += 1
        continue
    pid, tags, hints = row[0]
    n_tests = c.execute("select count(*) from test_cases where problem_id = ?", (pid,)).fetchone()[0]
    n_hidden = c.execute(
        "select count(*) from test_cases where problem_id = ? and is_hidden = 1", (pid,)
    ).fetchone()[0]
    total_tests += n_tests
    ok = bool(json.loads(tags or "[]")) and bool(json.loads(hints or "[]")) and n_tests > n_hidden > 0
    if not ok:
        bad += 1
    print(f"  {'OK ' if ok else 'BAD'} id={pid} {t} (tests={n_tests}, hidden={n_hidden})")
print()
print("Total tests in this batch:", total_tests)
print("Batch problems with issues:", bad)