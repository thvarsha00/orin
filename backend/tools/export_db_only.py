import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import CodingProblem, Topic

BANK = Path("app/services/coding/problem_bank/python.json")
OUT = Path("tools/batches/db_only_python_export.json")

bank_titles = {p["title"] for p in json.loads(BANK.read_text(encoding="utf-8"))}
print(f"python.json titles: {len(bank_titles)}")

export = []

with SessionLocal() as db:
    rows = db.scalars(
        select(CodingProblem)
        .where(
            CodingProblem.language == "python",
            CodingProblem.owner_id.is_(None),
        )
        .order_by(CodingProblem.id)
    ).all()
    print(f"Python problems in DB: {len(rows)}")

    for p in rows:
        if p.title in bank_titles:
            continue
        topic = db.get(Topic, p.topic_id)
        tests = sorted(p.test_cases, key=lambda t: t.id)
        hidden = sum(1 for t in tests if t.is_hidden)
        print(
            f"DB-only id={p.id} {p.title} | {topic.name} | {p.difficulty} | "
            f"tests={len(tests)} hidden={hidden} | "
            f"tags={len(p.tags or [])} hints={len(p.hints or [])} | "
            f"entry={p.entry_function}"
        )
        export.append(
            {
                "title": p.title,
                "topic": topic.name,
                "difficulty": p.difficulty,
                "description": p.description,
                "examples": p.examples or [],
                "constraints": p.constraints or "",
                "starter_code": p.starter_code,
                "entry_function": p.entry_function,
                "expected_complexity": p.expected_complexity,
                "tags": p.tags or [],
                "hints": p.hints or [],
                "tests": [
                    {
                        "input": t.input_data,
                        "output": t.expected_output,
                        "hidden": bool(t.is_hidden),
                    }
                    for t in tests
                ],
            }
        )

OUT.write_text(json.dumps(export, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(export)} problems to {OUT}")