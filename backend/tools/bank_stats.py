import sqlite3

c = sqlite3.connect("file:orin.db?mode=ro", uri=True)

print("Python problems by difficulty:")
for d, n in c.execute(
    "select difficulty, count(*) from coding_problems "
    "where language = 'python' group by difficulty order by count(*) desc"
):
    print(f"  {d}: {n}")

print()
print("Python problems by topic:")
for name, n in c.execute(
    "select t.name, count(*) from coding_problems p "
    "join topics t on t.id = p.topic_id "
    "where p.language = 'python' group by t.name order by count(*) desc, t.name"
):
    print(f"  {name}: {n}")