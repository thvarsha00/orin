import sqlite3

c = sqlite3.connect("orin.db")

print("Rows whose title is literally an alias title:")
rows = c.execute(
    "select id, title, language from coding_problems where title in (?, ?) order by id",
    ("IsPrime", "Most FrequentElement"),
).fetchall()
print("count:", len(rows))
for r in rows:
    print(r)

print()
print("Rows for the real titles:")
rows = c.execute(
    "select id, title, language from coding_problems where title in (?, ?) order by id",
    ("Is Prime", "Most Frequent Element"),
).fetchall()
print("count:", len(rows))
for r in rows:
    print(r)