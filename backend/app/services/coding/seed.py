"""Load coding problems from the Orin problem bank.

Run from the backend folder:

    python -m app.services.coding.seed
"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CodingProblem, TestCase, Topic


PROBLEM_BANK_DIR = Path(__file__).parent / "problem_bank"

LANGUAGE_FILES = {
    "python": "python.json",
    "javascript": "javascript.json",
}

TITLE_ALIASES = {
    ("python", "Is Prime"): "IsPrime",
    ("python", "Most Frequent Element"): "Most FrequentElement",
}


def load_problem_bank() -> list[dict]:
    problems = []

    for language, filename in LANGUAGE_FILES.items():
        path = PROBLEM_BANK_DIR / filename

        if not path.exists():
            print(f"Warning: problem bank not found: {path}")
            continue

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                f"{filename} must contain a JSON array."
            )

        for problem in data:
            problem["language"] = language
            problems.append(problem)

    return problems


def _existing_title(language: str, title: str) -> str:
    return TITLE_ALIASES.get(
        (language, title),
        title,
    )


def seed(db: Session) -> dict[str, int]:
    added = {
        "topics": 0,
        "problems": 0,
        "tests": 0,
    }

    problems = load_problem_bank()

    topics: dict[str, Topic] = {}

    # Pass 1: make sure every topic exists.
    for problem_data in problems:
        topic_name = problem_data["topic"]

        topic = db.scalar(
            select(Topic).where(Topic.name == topic_name)
        )

        if not topic:
            topic = Topic(name=topic_name)
            db.add(topic)
            db.flush()
            added["topics"] += 1

        topics[topic_name] = topic

    # Pass 2: add problems that do not exist yet.
    for problem_data in problems:
        language = problem_data["language"]
        real_title = problem_data["title"]
        alias_title = _existing_title(language, real_title)

        candidate_titles = [real_title]
        if alias_title != real_title:
            candidate_titles.append(alias_title)

        existing = db.scalar(
            select(CodingProblem)
            .where(
                CodingProblem.title.in_(candidate_titles),
                CodingProblem.language == language,
                CodingProblem.owner_id.is_(None),
            )
            .order_by(CodingProblem.id)
            .limit(1)
        )

        if existing:
            changed = False

            if not existing.tags:
                existing.tags = problem_data.get("tags", [])
                changed = True

            if not existing.hints:
                existing.hints = problem_data.get("hints", [])
                changed = True

            if changed:
                db.add(existing)

            continue

        problem = CodingProblem(
            title=real_title,
            description=problem_data["description"],
            difficulty=problem_data["difficulty"],
            topic_id=topics[problem_data["topic"]].id,
            language=language,
            examples=problem_data.get("examples", []),
            tags=problem_data.get("tags", []),
            hints=problem_data.get("hints", []),
            constraints=problem_data.get("constraints", ""),
            starter_code=problem_data["starter_code"],
            entry_function=problem_data.get(
                "entry_function",
                "solve",
            ),
            expected_complexity=problem_data.get(
                "expected_complexity"
            ),
            status="published",
            owner_id=None,
        )

        test_cases = problem_data.get("tests", [])

        problem.test_cases = [
            TestCase(
                input_data=test["input"],
                expected_output=test["output"],
                is_hidden=test.get("hidden", False),
            )
            for test in test_cases
        ]

        added["tests"] += len(test_cases)

        db.add(problem)
        added["problems"] += 1

    db.commit()

    return added


if __name__ == "__main__":
    from app.database import SessionLocal, init_db

    init_db()

    with SessionLocal() as session:
        result = seed(session)

    print(
        f"Seeded: "
        f"{result['topics']} new topics, "
        f"{result['problems']} new problems, "
        f"{result['tests']} new tests."
    )