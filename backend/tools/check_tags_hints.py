import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import CodingProblem

with SessionLocal() as db:
    rows = db.scalars(
        select(CodingProblem)
        .where(CodingProblem.id <= 5)
        .order_by(CodingProblem.id)
    ).all()
    for p in rows:
        print(
            f"id={p.id} {p.title} | tags={len(p.tags or [])} "
            f"hints={len(p.hints or [])}"
        )