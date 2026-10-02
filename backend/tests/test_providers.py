import asyncio
import json

import httpx
import pytest

from app.services.ai.base import AIError
from app.services.ai.openai_compat import OpenAICompatProvider


def make(handler, key="gsk_test", model="openai/gpt-oss-120b"):
    return OpenAICompatProvider("groq", "https://api.groq.com/openai/v1", key, model, "GROQ_API_KEY",
                                transport=httpx.MockTransport(handler))


def sse(*chunks):
    lines = [f"data: {json.dumps({'choices': [{'delta': {'content': c}}]})}\n\n" for c in chunks]
    return "".join(lines) + "data: [DONE]\n\n"


async def collect(agen):
    return [c async for c in agen]


def test_stream_parses_sse_and_sends_auth_and_settings():
    seen = {}

    def handler(req: httpx.Request):
        seen["auth"] = req.headers["authorization"]
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, text=sse("Tuple ", "ante ", "..."))

    out = asyncio.run(collect(make(handler).stream([{"role": "user", "content": "hi"}])))
    assert "".join(out) == "Tuple ante ..."
    assert seen["auth"] == "Bearer gsk_test"
    assert seen["body"]["stream"] is True and seen["body"]["reasoning_effort"] == "low"


@pytest.mark.parametrize("status,needle", [(401, "rejected the API key"), (429, "rate limit"),
                                           (404, "could not use model"), (500, "problem")])
def test_http_errors_become_friendly_messages(status, needle):
    p = make(lambda req: httpx.Response(status, json={"error": "x"}))
    with pytest.raises(AIError) as e:
        asyncio.run(p.chat([{"role": "user", "content": "hi"}]))
    assert needle in e.value.message


def test_missing_key_is_reported_before_any_request():
    p = make(lambda req: pytest.fail("no request expected"), key="")
    with pytest.raises(AIError) as e:
        asyncio.run(collect(p.stream([{"role": "user", "content": "hi"}])))
    assert "GROQ_API_KEY" in e.value.message


def test_chat_json_and_health():
    def handler(req: httpx.Request):
        if req.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "openai/gpt-oss-120b"}]})
        assert json.loads(req.content)["response_format"] == {"type": "json_object"}
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok": true}'}}]})

    p = make(handler)
    assert asyncio.run(p.chat_json([{"role": "user", "content": "x"}])) == {"ok": True}
    h = asyncio.run(p.health())
    assert h["reachable"] and h["chat_model_available"] and h["hint"] is None
    assert not asyncio.run(make(handler, model="nope").health())["chat_model_available"]
