import os

os.environ["DATABASE_URL"] = "sqlite:///./test_orin.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


def setup_module():
    Base.metadata.drop_all(bind=engine)


def teardown_module():
    engine.dispose()
    if os.path.exists("test_orin.db"):
        os.remove("test_orin.db")


def test_health_and_auth_flow():
    with TestClient(app) as c:
        h = c.get("/api/health").json()
        assert h["status"] == "ok" and "ai" in h

        r = c.post("/api/auth/register", json={"email": "v@example.com", "password": "password123",
                                               "display_name": "Varsha", "preferred_language": "te"})
        assert r.status_code == 201
        token = r.json()["access_token"]
        assert r.json()["user"]["profile"]["preferred_language"] == "te"

        dup = {"email": "v@example.com", "password": "password123", "display_name": "V"}
        assert c.post("/api/auth/register", json=dup).status_code == 409
        assert c.post("/api/auth/login", json={"email": "v@example.com", "password": "wrong"}).status_code == 401

        hdr = {"Authorization": f"Bearer {token}"}
        assert c.get("/api/auth/me", headers=hdr).json()["profile"]["display_name"] == "Varsha"
        assert c.get("/api/auth/me").status_code == 401
        up = c.patch("/api/auth/me/profile", headers=hdr, json={"skill_level": "advanced"})
        assert up.json()["profile"]["skill_level"] == "advanced"


def test_tutor_friendly_error_when_ollama_down():
    from app.config import settings
    from app.services import ai
    settings.ai_provider = "groq"
    settings.groq_api_key = ""            # no key configured
    ai.get_ai.cache_clear()
    with TestClient(app) as c:
        token = c.post("/api/auth/login",
                       json={"email": "v@example.com", "password": "password123"}).json()["access_token"]
        r = c.post("/api/tutor/chat", headers={"Authorization": f"Bearer {token}"},
                   json={"message": "Python lo list ante enti?", "language": "te"})
        assert r.status_code == 503
        assert "GROQ_API_KEY" in r.json()["error"]
        assert "Traceback" not in r.text
