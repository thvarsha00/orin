import shutil
import sqlite3
import sys

KEEP = {"Is Prime": 20, "Most Frequent Element": 24}
DELETE_IDS = [29, 30, 31, 32, 43, 44, 55, 56]
apply = "--apply" in sys.argv

c = sqlite3.connect("orin.db")

# Safety checks: every target must be a python duplicate of a kept row,
# with no submissions and no daily challenges.
for pid in DELETE_IDS:
    row = c.execute("select title, language from coding_problems where id = ?", (pid,)).fetchone()
    if row is None:
        raise SystemExit(f"ID {pid} not found. Stopping.")
    title, lang = row
    if title not in KEEP or lang != "python":
        raise SystemExit(f"ID {pid} is '{title}' ({lang}), not an expected duplicate. Stopping.")
    if c.execute("select count(*) from submissions where problem_id = ?", (pid,)).fetchone()[0]:
        raise SystemExit(f"ID {pid} has submissions. Stopping.")
    if c.execute("select count(*) from daily_challenges where problem_id = ?", (pid,)).fetchone()[0]:
        raise SystemExit(f"ID {pid} has daily challenges. Stopping.")

for title, kid in KEEP.items():
    if c.execute("select count(*) from coding_problems where id = ?", (kid,)).fetchone()[0] != 1:
        raise SystemExit(f"Kept row {kid} ({title}) is missing. Stopping.")

marks = ",".join("?" * len(DELETE_IDS))
n_tests = c.execute(f"select count(*) from test_cases where problem_id in ({marks})", DELETE_IDS).fetchone()[0]
before = c.execute("select count(*) from coding_problems").fetchone()[0]
print(f"Safety checks passed. Would delete {len(DELETE_IDS)} problems and {n_tests} test cases.")
print(f"coding_problems now: {before}, after: {before - len(DELETE_IDS)}")

if not apply:
    print("Dry run only. Nothing changed. Re-run with --apply to delete.")
    raise SystemExit(0)

c.close()
shutil.copyfile("orin.db", "orin.db.bak_before_dedupe")
print("Backup saved: orin.db.bak_before_dedupe")

c = sqlite3.connect("orin.db")
c.execute(f"delete from test_cases where problem_id in ({marks})", DELETE_IDS)
c.execute(f"delete from coding_problems where id in ({marks})", DELETE_IDS)
c.commit()
print("Deleted. coding_problems now:", c.execute("select count(*) from coding_problems").fetchone()[0])