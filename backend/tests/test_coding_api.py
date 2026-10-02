"""Orin Code API tests: uses the local subprocess runner (no Docker needed) and a throwaway SQLite file."""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_orin.db"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import CodingProblem, SubmissionResult, TestCase, Topic  # noqa: E402
from app.services.coding import executor  # noqa: E402
from app.services.coding.seed import seed  # noqa: E402

EVEN_OK = "def solve(nums):\n    return sum(n for n in nums if n % 2 == 0)"
# Passes every visible test but fails the hidden 10**6 case, so only Submit catches it.
EVEN_CHEAT = "def solve(nums):\n    return sum(n for n in nums if n % 2 == 0 and n < 1000)"


def setup_module():
    Base.metadata.drop_all(bind=engine)
    settings.code_runner = "subprocess"
    settings.code_time_limit_seconds = 1.0


def teardown_module():
    engine.dispose()
    if os.path.exists("test_orin.db"):
        os.remove("test_orin.db")


def _user(c, email):
    r = c.post("/api/auth/register", json={"email": email, "password": "password123", "display_name": "T"})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _problem_id(c, hdr, title):
    return next(p["id"] for p in c.get("/api/coding/problems", headers=hdr).json() if p["title"] == title)


def test_seed_is_idempotent_and_endpoints_need_login():
    with TestClient(app) as c:
        with SessionLocal() as db:
            first = seed(db)
            second = seed(db)
        assert first == {"topics": 2, "problems": 5} and second == {"topics": 0, "problems": 0}
        assert c.get("/api/coding/problems").status_code == 401
        assert c.post("/api/coding/run", json={"problem_id": 1, "code": "x"}).status_code == 401


def test_problem_detail_never_exposes_hidden_tests():
    with TestClient(app) as c:
        hdr = _user(c, "detail@example.com")
        listing = c.get("/api/coding/problems", headers=hdr).json()
        assert len(listing) == 5 and {"id", "title", "difficulty", "topic"} <= set(listing[0])
        pid = _problem_id(c, hdr, "Sum of Even Numbers")
        body = c.get(f"/api/coding/problems/{pid}", headers=hdr).json()
        assert body["visible_tests"] == 3 and body["hidden_tests"] == 2
        assert body["entry_function"] == "solve" and "def solve" in body["starter_code"]
        assert "test_cases" not in body and "1000002" not in c.get(f"/api/coding/problems/{pid}", headers=hdr).text


def test_run_uses_visible_tests_only_and_saves_nothing():
    with TestClient(app) as c:
        hdr = _user(c, "run@example.com")
        pid = _problem_id(c, hdr, "Sum of Even Numbers")
        ok = c.post("/api/coding/run", headers=hdr, json={"problem_id": pid, "code": EVEN_OK}).json()
        assert (ok["status"], ok["passed"], ok["total"]) == ("passed", 3, 3)
        assert all(not r["hidden"] and r["input"] is not None for r in ok["results"])

        wrong = c.post("/api/coding/run", headers=hdr,
                       json={"problem_id": pid, "code": "def solve(nums):\n    return 0"}).json()
        assert wrong["status"] == "failed" and wrong["passed"] < wrong["total"]
        failing = next(r for r in wrong["results"] if not r["passed"])
        assert failing["expected"] is not None and failing["actual"] == "0"

        with SessionLocal() as db:
            assert db.scalar(select(func.count()).select_from(SubmissionResult)) == 0


def test_run_reports_syntax_errors_and_timeouts():
    with TestClient(app) as c:
        hdr = _user(c, "errors@example.com")
        pid = _problem_id(c, hdr, "Sum of Even Numbers")
        bad = c.post("/api/coding/run", headers=hdr, json={"problem_id": pid, "code": "def solve(:"}).json()
        assert bad["status"] == "error" and "SyntaxError" in bad["error"]
        loop = c.post("/api/coding/run", headers=hdr,
                      json={"problem_id": pid, "code": "def solve(nums):\n    while True:\n        pass"}).json()
        assert loop["status"] == "timeout" and loop["results"][0]["timed_out"] is True


def test_submit_judges_hidden_tests_hides_their_contents_and_saves_the_attempt():
    with TestClient(app) as c:
        hdr = _user(c, "submit@example.com")
        pid = _problem_id(c, hdr, "Sum of Even Numbers")

        cheat = c.post("/api/coding/submit", headers=hdr, json={"problem_id": pid, "code": EVEN_CHEAT}).json()
        assert cheat["status"] == "failed" and (cheat["passed"], cheat["total"]) == (4, 5)
        hidden = [r for r in cheat["results"] if r["hidden"]]
        assert len(hidden) == 2
        assert all(r["input"] is None and r["expected"] is None and r["actual"] is None for r in hidden)
        assert any(r["error"] == "Wrong answer" for r in hidden)

        good = c.post("/api/coding/submit", headers=hdr, json={"problem_id": pid, "code": EVEN_OK}).json()
        assert (good["status"], good["passed"], good["total"]) == ("passed", 5, 5)

        history = c.get(f"/api/coding/problems/{pid}/submissions", headers=hdr).json()
        assert [s["status"] for s in history] == ["passed", "failed"]      # newest first
        with SessionLocal() as db:
            assert db.scalar(select(func.count()).select_from(SubmissionResult)
                             .where(SubmissionResult.submission_id == good["submission_id"])) == 5


def test_draft_problems_are_private_to_their_owner():
    with TestClient(app) as c:
        owner, other = _user(c, "owner@example.com"), _user(c, "other@example.com")
        owner_id = c.get("/api/auth/me", headers=owner).json()["id"]
        with SessionLocal() as db:
            topic = db.scalar(select(Topic))
            draft = CodingProblem(title="Private draft", description="d", difficulty="easy", topic_id=topic.id,
                                  status="draft", owner_id=owner_id, starter_code="def solve(a):\n    pass\n")
            draft.test_cases = [TestCase(input_data=[1], expected_output=1)]
            db.add(draft)
            db.commit()
            pid = draft.id
        assert c.get(f"/api/coding/problems/{pid}", headers=owner).status_code == 200
        assert c.get(f"/api/coding/problems/{pid}", headers=other).status_code == 404
        assert c.post("/api/coding/run", headers=other, json={"problem_id": pid, "code": "x"}).status_code == 404
        assert "Private draft" not in [p["title"] for p in c.get("/api/coding/problems", headers=other).json()]


def test_input_validation_and_missing_docker_give_clear_errors(monkeypatch):
    with TestClient(app) as c:
        hdr = _user(c, "validate@example.com")
        pid = _problem_id(c, hdr, "Sum of Even Numbers")
        java = c.post("/api/coding/run", headers=hdr, json={"problem_id": pid, "code": "x", "language": "java"})
        assert java.status_code == 422 and "Python" in java.json()["error"]
        too_long = c.post("/api/coding/run", headers=hdr, json={"problem_id": pid, "code": "x" * 20_001})
        assert too_long.status_code == 422
        assert c.post("/api/coding/run", headers=hdr, json={"problem_id": 99999, "code": "x"}).status_code == 404

        monkeypatch.setattr(settings, "code_runner", "docker")
        monkeypatch.setattr(executor.shutil, "which", lambda _name: None)
        r = c.post("/api/coding/run", headers=hdr, json={"problem_id": pid, "code": EVEN_OK})
        assert r.status_code == 503 and "Docker" in r.json()["error"]
