import asyncio
import json
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_orin.db"

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.services import ai, images  # noqa: E402
from app.services.ai.base import AIError  # noqa: E402
from app.services.ai.ollama import _to_ollama_messages  # noqa: E402
from app.services.ai.openai_compat import OpenAICompatProvider  # noqa: E402
from app.services.ai.utils import strip_think  # noqa: E402
from app.services.language import LANGUAGES, build_system_prompt, resolve_profile  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 32


def setup_module():
    Base.metadata.drop_all(bind=engine)


def teardown_module():
    engine.dispose()
    if os.path.exists("test_orin.db"):
        os.remove("test_orin.db")


class Fake:
    """Stands in for a provider at the network boundary; records exactly what it is sent."""
    def __init__(self, reply="Step 1\nAnswer"):
        self.reply, self.calls = reply, []

    async def stream(self, messages):
        self.calls.append(messages)
        for i in range(0, len(self.reply), 5):
            yield self.reply[i:i + 5]


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "up"))
    monkeypatch.setattr(settings, "max_image_mb", 1.0)
    vision, text = Fake("Here is the worked solution."), Fake("Text answer.")
    monkeypatch.setattr("app.api.tutor.get_vision_ai", lambda: vision)
    monkeypatch.setattr("app.api.tutor.get_ai", lambda: text)
    with TestClient(app) as c:
        def login(email):
            r = c.post("/api/auth/register", json={"email": email, "password": "password123", "display_name": "T"})
            return {"Authorization": f"Bearer {r.json()['access_token']}"}
        yield c, login, vision, text


def send(c, hdr, file=("a.png", PNG, "image/png"), **form):
    form.setdefault("message", "")
    return c.post("/api/tutor/chat/image", headers=hdr, data=form, files={"image": file} if file else None)


# ---- validation ---------------------------------------------------------------------------
@pytest.mark.parametrize("data,mime", [(PNG, "image/png"), (JPG, "image/jpeg"), (WEBP, "image/webp")])
def test_accepts_png_jpg_webp(data, mime):
    assert images.validate(data) == mime


def test_rejects_wrong_type_empty_and_oversized(monkeypatch):
    monkeypatch.setattr(settings, "max_image_mb", 1.0)
    for bad in (b"GIF89a....", b"%PDF-1.7", b"MZ\x90\x00"):
        with pytest.raises(images.ImageError) as e:
            images.validate(bad)
        assert e.value.status_code == 415 and "JPG, PNG or WEBP" in e.value.message
    with pytest.raises(images.ImageError):
        images.validate(b"")
    with pytest.raises(images.ImageError) as e:
        images.validate(PNG + b"0" * (1024 * 1024))
    assert e.value.status_code == 413 and "1 MB" in e.value.message


# ---- endpoint -----------------------------------------------------------------------------
def test_image_with_question_reaches_vision_model_and_persists(env):
    c, login, vision, text = env
    hdr = login("a@x.com")
    r = send(c, hdr, message="Solve this", language="te", script="roman")
    assert r.status_code == 200 and r.text == "Here is the worked solution."
    conv = int(r.headers["X-Conversation-Id"])

    msgs = vision.calls[0]
    assert text.calls == []                                   # text model never sees image turns
    assert "Language: Telugu" in msgs[0]["content"] and "Script: Roman" in msgs[0]["content"]
    parts = msgs[-1]["content"]
    assert parts[0] == {"type": "text", "text": "Solve this"}
    assert parts[1]["image_url"]["url"].startswith("data:image/png;base64,")

    stored = c.get(f"/api/tutor/conversations/{conv}/messages", headers=hdr).json()
    assert [m["role"] for m in stored] == ["user", "assistant"]
    assert stored[0]["has_image"] is True and stored[1]["has_image"] is False
    img = c.get(f"/api/tutor/messages/{stored[0]['id']}/image", headers=hdr)
    assert img.status_code == 200 and img.content == PNG and img.headers["content-type"] == "image/png"
    assert "base64" not in json.dumps(stored)                # never leaks image bytes into chat JSON


def test_image_only_message(env):
    c, login, vision, _ = env
    hdr = login("b@x.com")
    r = send(c, hdr, language="hi", script="native")
    assert r.status_code == 200
    assert "without a question" in vision.calls[0][-1]["content"][0]["text"]
    conv = int(r.headers["X-Conversation-Id"])
    assert c.get("/api/tutor/conversations", headers=hdr).json()[0]["title"] == "Image question"
    assert c.get(f"/api/tutor/conversations/{conv}/messages", headers=hdr).json()[0]["content"] == ""


def test_bad_uploads_get_clear_errors_and_nothing_is_saved(env):
    c, login, vision, _ = env
    hdr = login("c@x.com")
    r = send(c, hdr, file=("x.gif", b"GIF89a....", "image/gif"))
    assert r.status_code == 415 and "JPG, PNG or WEBP" in r.json()["error"]
    r = send(c, hdr, file=("x.png", PNG + b"0" * (1024 * 1024), "image/png"))
    assert r.status_code == 413 and "limit" in r.json()["error"]
    r = send(c, hdr, file=("x.png", b"", "image/png"))
    assert r.status_code == 400
    assert send(c, hdr, file=None).status_code == 422
    assert vision.calls == [] and c.get("/api/tutor/conversations", headers=hdr).json() == []


def test_lying_content_type_is_not_trusted(env):
    c, login, vision, _ = env
    r = send(c, login("d@x.com"), file=("evil.png", b"%PDF-1.7 not an image", "image/png"))
    assert r.status_code == 415 and vision.calls == []


def test_text_followup_after_image_uses_text_model_and_marks_history(env):
    c, login, vision, text = env
    hdr = login("e@x.com")
    conv = send(c, hdr, message="Explain").headers["X-Conversation-Id"]
    r = c.post("/api/tutor/chat", headers=hdr, json={"message": "why?", "conversation_id": int(conv)})
    assert r.status_code == 200 and r.text == "Text answer."
    call = text.calls[0]
    assert any("[image attached]" in m["content"] for m in call[1:-1])
    assert "cannot see those images" in call[0]["content"]
    assert call[-1] == {"role": "user", "content": "why?"}
    assert len(vision.calls) == 1


def test_text_only_chat_unchanged(env):
    c, login, vision, text = env
    hdr = login("f@x.com")
    r = c.post("/api/tutor/chat", headers=hdr, json={"message": "hello", "language": "te"})
    assert r.status_code == 200 and vision.calls == []
    assert "cannot see those images" not in text.calls[0][0]["content"]
    assert "worked solution" not in text.calls[0][0]["content"]


def test_images_are_private_per_user_and_deleted_with_conversation(env):
    c, login, *_ = env
    a, b = login("g@x.com"), login("h@x.com")
    conv = int(send(c, a, message="hi").headers["X-Conversation-Id"])
    mid = c.get(f"/api/tutor/conversations/{conv}/messages", headers=a).json()[0]["id"]
    assert c.get(f"/api/tutor/messages/{mid}/image", headers=b).status_code == 404
    assert c.get(f"/api/tutor/messages/{mid}/image").status_code == 401
    files = [p for p in images.root().rglob("*") if p.is_file()]
    assert len(files) == 1
    assert c.delete(f"/api/tutor/conversations/{conv}", headers=a).status_code == 204
    assert not [p for p in images.root().rglob("*") if p.is_file()]


def test_vision_model_not_configured_is_a_clear_error_and_never_falls_back(env, monkeypatch):
    c, login, vision, text = env
    monkeypatch.undo()                                        # use the real factory
    monkeypatch.setattr(settings, "upload_dir", str(images.root()))
    monkeypatch.setattr(settings, "vision_provider", "xai")
    monkeypatch.setattr(settings, "xai_vision_model", "")
    ai.get_vision_ai.cache_clear()
    r = send(c, login("i@x.com"), message="what is this")
    assert r.status_code == 503 and "XAI_VISION_MODEL" in r.json()["error"]
    assert c.get("/api/tutor/conversations", headers=login("j@x.com")).json() == []


def test_health_reports_vision(monkeypatch):
    monkeypatch.setattr(settings, "vision_provider", "")
    monkeypatch.setattr(settings, "ai_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "")
    v = ai.vision_status()
    assert v["provider"] == "groq" and v["model"] == "qwen/qwen3.8-27b" and not v["configured"]
    monkeypatch.setattr(settings, "groq_api_key", "gsk_x")
    assert ai.vision_status()["configured"] is True


def test_vision_health_checks_model_exists_on_account(monkeypatch):
    def handler(req):
        return httpx.Response(200, json={"data": [{"id": "openai/gpt-oss-120b"}]})   # vision model NOT listed

    fake = OpenAICompatProvider("groq", "https://api.groq.com/openai/v1", "gsk_x", "qwen/qwen3.8-27b", "GROQ_API_KEY",
                                transport=httpx.MockTransport(handler), vision=True)
    monkeypatch.setattr(settings, "vision_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "gsk_x")
    monkeypatch.setattr(ai, "get_vision_ai", lambda: fake)
    info = asyncio.run(ai.vision_health())
    assert info["configured"] and info["reachable"] and info["available"] is False
    assert "not available on your account" in info["hint"]


# ---- provider wire format -----------------------------------------------------------------
def vision_provider(handler):
    return OpenAICompatProvider("groq", "https://api.groq.com/openai/v1", "gsk_test", "qwen/qwen3.8-27b",
                                "GROQ_API_KEY", transport=httpx.MockTransport(handler), vision=True,
                                model_env_name="GROQ_VISION_MODEL")


def sse(*chunks):
    return "".join(f"data: {json.dumps({'choices': [{'delta': {'content': c}}]})}\n\n" for c in chunks) + "data: [DONE]\n\n"


def test_openai_compat_sends_image_parts_and_strips_thinking():
    seen = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, text=sse("<thi", "nk>secret reason", "ing</th", "ink>\n\nThe answer ", "is 4."))

    msgs = [{"role": "user", "content": [{"type": "text", "text": "2+2?"},
                                         {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]}]

    async def run():
        return "".join([c async for c in vision_provider(handler).stream(msgs)])

    assert asyncio.run(run()) == "The answer is 4."
    assert seen["body"]["model"] == "qwen/qwen3.8-27b"
    assert seen["body"]["messages"][0]["content"][1]["image_url"]["url"] == "data:image/png;base64,AAAA"
    assert "reasoning_effort" not in seen["body"]


@pytest.mark.parametrize("status", [400, 413, 422])
def test_vision_http_errors_mention_the_image(status):
    p = vision_provider(lambda req: httpx.Response(status, json={"error": "x"}))

    async def run():
        return [c async for c in p.stream([{"role": "user", "content": "hi"}])]

    with pytest.raises(AIError) as e:
        asyncio.run(run())
    assert "could not process this image" in e.value.message and "GROQ_VISION_MODEL" in e.value.message


def test_strip_think_passes_plain_text_untouched():
    async def gen():
        for c in ("a < b ", "and <b>bold</b> ", "<"):
            yield c

    async def run():
        return "".join([c async for c in strip_think(gen())])

    assert asyncio.run(run()) == "a < b and <b>bold</b> <"


def test_ollama_conversion():
    out = _to_ollama_messages([
        {"role": "system", "content": "s"},
        {"role": "user", "content": [{"type": "text", "text": "q"},
                                     {"type": "image_url", "image_url": {"url": "data:image/png;base64,QUJD"}}]}])
    assert out[0] == {"role": "system", "content": "s"}
    assert out[1] == {"role": "user", "content": "q", "images": ["QUJD"]}


# ---- multilingual prompt ------------------------------------------------------------------
@pytest.mark.parametrize("code", list(LANGUAGES))
@pytest.mark.parametrize("pref", ["native", "roman", "auto"])
def test_image_prompt_honours_language_and_script_for_every_language(code, pref):
    prof, _ = resolve_profile(code, "", pref)
    prompt = build_system_prompt("image", prof, "beginner")
    assert f"Language: {LANGUAGES[code].name}" in prompt
    if code != "en" and pref == "native":
        assert f"Script: Native ({LANGUAGES[code].native_script_name})" in prompt
    if code != "en" and pref == "roman":
        assert "Script: Roman" in prompt
    assert "do not just describe it" in prompt and "Never guess or invent" in prompt
    assert "do NOT give the full solution" not in prompt       # solving from images is allowed
