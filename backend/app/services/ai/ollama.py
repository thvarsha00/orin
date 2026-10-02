import json
from typing import AsyncIterator

import httpx

from app.config import settings
from app.services.ai.base import AIError, AIProvider

UNREACHABLE = "Can't reach Ollama. Make sure it is running (ollama serve)."
SLOW = "The AI model is taking too long to respond. Try again or use a smaller model."


def _to_ollama_messages(messages: list[dict]) -> list[dict]:
    """Accepts OpenAI-style content parts (text + image_url data URLs) and converts them to Ollama's
    {"content": str, "images": [base64, ...]} shape. Plain string messages pass through unchanged."""
    out = []
    for m in messages:
        content = m.get("content")
        if not isinstance(content, list):
            out.append(m)
            continue
        text = "\n".join(p.get("text", "") for p in content if p.get("type") == "text")
        images = []
        for p in content:
            if p.get("type") == "image_url":
                url = p["image_url"]["url"]
                images.append(url.split(",", 1)[1] if url.startswith("data:") else url)
        msg = {"role": m["role"], "content": text}
        if images:
            msg["images"] = images
        out.append(msg)
    return out


def _has_images(messages: list[dict]) -> bool:
    return any(isinstance(m.get("content"), list) and any(p.get("type") == "image_url" for p in m["content"])
               for m in messages)


class OllamaProvider(AIProvider):
    def __init__(self, base_url: str | None = None, model: str | None = None, embed_model: str | None = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.embed_model = embed_model or settings.ollama_embed_model
        self.timeout = httpx.Timeout(settings.ollama_timeout_seconds, connect=5.0)

    def _payload(self, messages: list[dict], stream: bool, **extra) -> dict:
        options = {"temperature": settings.ollama_temperature, "repeat_penalty": settings.ollama_repeat_penalty}
        return {"model": self.model, "messages": _to_ollama_messages(messages), "stream": stream,
                "options": options, **extra}

    @staticmethod
    def _raise_for(resp: httpx.Response, model: str, images: bool = False) -> None:
        if resp.status_code == 404:
            raise AIError(f"Model '{model}' is not installed. Run: ollama pull {model}", 503)
        if resp.status_code == 400 and images:
            raise AIError(f"Ollama model '{model}' could not process the image. Make sure OLLAMA_VISION_MODEL "
                          f"is a vision model (e.g. qwen2.5vl:7b or llava) and the image is valid.", 502)
        if resp.status_code >= 400:
            raise AIError("The AI model returned an error. Please try again.", 502)

    async def chat(self, messages: list[dict]) -> str:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=self._payload(messages, False))
            self._raise_for(resp, self.model, _has_images(messages))
            return resp.json()["message"]["content"]
        except httpx.ConnectError:
            raise AIError(UNREACHABLE)
        except httpx.TimeoutException:
            raise AIError(SLOW, 504)

    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat",
                                         json=self._payload(messages, True)) as resp:
                    if resp.status_code >= 400:
                        await resp.aread()
                        self._raise_for(resp, self.model, _has_images(messages))
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                        if data.get("done"):
                            break
        except httpx.ConnectError:
            raise AIError(UNREACHABLE)
        except httpx.TimeoutException:
            raise AIError(SLOW, 504)

    async def chat_json(self, messages: list[dict], schema: dict | None = None, retries: int = 1) -> dict:
        """Ask for JSON; retry because small local models sometimes emit invalid JSON."""
        fmt = schema if schema else "json"
        last_err = ""
        for _ in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(f"{self.base_url}/api/chat",
                                             json=self._payload(messages, False, format=fmt))
                self._raise_for(resp, self.model)
                return json.loads(resp.json()["message"]["content"])
            except json.JSONDecodeError as e:
                last_err = str(e)
            except httpx.ConnectError:
                raise AIError(UNREACHABLE)
            except httpx.TimeoutException:
                raise AIError(SLOW, 504)
        raise AIError(f"The AI returned invalid structured data ({last_err}). Please retry.", 502)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/api/embed",
                                         json={"model": self.embed_model, "input": texts})
            self._raise_for(resp, self.embed_model)
            return resp.json()["embeddings"]
        except httpx.ConnectError:
            raise AIError(UNREACHABLE)
        except httpx.TimeoutException:
            raise AIError("Embedding timed out.", 504)

    async def health(self) -> dict:
        result = {"provider": "ollama", "reachable": False, "base_url": self.base_url, "chat_model": self.model,
                  "embed_model": self.embed_model, "chat_model_available": False,
                  "embed_model_available": False, "hint": None}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(3.0)) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
            resp.raise_for_status()
        except httpx.HTTPError:
            result["hint"] = "Ollama is not running. Start it with `ollama serve`."
            return result
        result["reachable"] = True
        installed = {m["name"] for m in resp.json().get("models", [])}
        installed |= {n.split(":")[0] for n in installed if n.endswith(":latest")}
        result["chat_model_available"] = self.model in installed
        result["embed_model_available"] = self.embed_model in installed
        missing = [m for m, ok in ((self.model, result["chat_model_available"]),
                                   (self.embed_model, result["embed_model_available"])) if not ok]
        if missing:
            result["hint"] = "Missing models. Run: " + " && ".join(f"ollama pull {m}" for m in missing)
        return result
