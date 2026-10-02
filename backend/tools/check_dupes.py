import sqlite3

DUP_IDS = [20, 24, 29, 30, 31, 32, 43, 44, 55, 56]

c = sqlite3.connect("file:orin.db?mode=ro", uri=True)

tables = [r[0] for r in c.execute(
    "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name"
)]

links = []
for t in tables:
    if t == "coding_problems":
        continue
    fk_cols = [r[3] for r in c.execute(f"pragma foreign_key_list({t})") if r[2] == "coding_problems"]
    name_cols = [r[1] for r in c.execute(f"pragma table_info({t})") if r[1] == "problem_id"]
    for col in sorted(set(fk_cols + name_cols)):
        links.append((t, col))

print("Tables that reference a problem:")
for t, col in links:
    print(f"  {t}.{col}")
print()

header = "id".ljust(6) + "".join(f"{t}".ljust(22) for t, _ in links)
print(header)
for pid in DUP_IDS:
    row = str(pid).ljust(6)
    for t, col in links:
        n = c.execute(f"select count(*) from {t} where {col} = ?", (pid,)).fetchone()[0]
        row += str(n).ljust(22)
    print(row)