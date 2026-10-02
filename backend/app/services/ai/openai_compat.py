"""Provider for any OpenAI-compatible chat API: Groq, xAI Grok, and others."""
import json
from typing import AsyncIterator

import httpx

from app.config import settings
from app.services.ai.base import AIError, AIProvider
from app.services.ai.utils import strip_think


class OpenAICompatProvider(AIProvider):
    def __init__(self, name: str, base_url: str, api_key: str, model: str,
                 key_env_name: str, transport: httpx.AsyncBaseTransport | None = None,
                 vision: bool = False, model_env_name: str = ""):
        self.vision = vision                    # True = this instance serves image questions
        self.model_env_name = model_env_name
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.key_env_name = key_env_name
        self.transport = transport
        self.timeout = httpx.Timeout(settings.ai_timeout_seconds, connect=8.0)

    # ---- helpers -------------------------------------------------------
    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout, transport=self.transport)

    def _headers(self) -> dict:
        if not self.api_key:
            raise AIError(f"{self.key_env_name} is not set. Add it to backend/.env and restart the backend.", 503)
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _body(self, messages: list[dict], stream: bool, **extra) -> dict:
        body = {"model": self.model, "messages": messages, "stream": stream,
                "temperature": settings.ai_temperature, **extra}
        if self.model.startswith("openai/gpt-oss") and settings.ai_reasoning_effort:
            body["reasoning_effort"] = settings.ai_reasoning_effort   # keep replies fast
        return body

    def _raise_for(self, status: int) -> None:
        if status < 400:
            return
        label = self.name.capitalize()
        if self.vision and status in (400, 413, 415, 422):
            raise AIError(f"{label} could not process this image. Try a smaller, clearer JPG, PNG or WEBP. "
                          f"If it keeps failing, check that {self.model_env_name or 'the vision model'} "
                          f"('{self.model}') supports image input.", 502)
        if status in (401, 403):
            raise AIError(f"{label} rejected the API key. Check {self.key_env_name} in backend/.env.", 503)
        if status == 404 or status == 400:
            raise AIError(f"{label} could not use model '{self.model}'. Check the model name in backend/.env.", 503)
        if status == 429:
            raise AIError(f"{label} rate limit reached. Wait a few seconds and try again.", 429)
        raise AIError(f"{label} had a problem ({status}). Please try again.", 502)

    def _network(self, exc: Exception) -> AIError:
        if isinstance(exc, httpx.TimeoutException):
            return AIError("The AI took too long to respond. Please try again.", 504)
        return AIError(f"Can't reach {self.name.capitalize()}. Check your internet connection.", 503)

    # ---- AIProvider API ------------------------------------------------
    async def chat(self, messages: list[dict]) -> str:
        try:
            async with self._client() as client:
                resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers(),
                                         json=self._body(messages, False))
            self._raise_for(resp.status_code)
            return resp.json()["choices"][0]["message"]["content"] or ""
        except httpx.HTTPError as e:
            raise self._network(e)

    async def stream(self, messages: list[dict]) -> AsyncIterator[str]:
        if self.vision:  # vision/reasoning models may emit <think> blocks inline; students shouldn't see them
            async for piece in strip_think(self._stream_raw(messages)):
                yield piece
        else:
            async for piece in self._stream_raw(messages):
                yield piece

    async def _stream_raw(self, messages: list[dict]) -> AsyncIterator[str]:
        try:
            async with self._client() as client:
                async with client.stream("POST", f"{self.base_url}/chat/completions", headers=self._headers(),
                                         json=self._body(messages, True)) as resp:
                    if resp.status_code >= 400:
                        await resp.aread()
                        self._raise_for(resp.status_code)
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        choices = json.loads(payload).get("choices") or []
                        chunk = choices[0].get("delta", {}).get("content") if choices else None
                        if chunk:
                            yield chunk
        except httpx.HTTPError as e:
            raise self._network(e)

    async def chat_json(self, messages: list[dict], schema: dict | None = None, retries: int = 1) -> dict:
        # json_object mode requires the word "JSON" to appear in the prompt.
        msgs = [*messages, {"role": "system", "content": "Respond with a single valid JSON object only."}]
        last = ""
        for _ in range(retries + 1):
            try:
                async with self._client() as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions", headers=self._headers(),
                        json=self._body(msgs, False, response_format={"type": "json_object"}))
                self._raise_for(resp.status_code)
                return json.loads(resp.json()["choices"][0]["message"]["content"])
            except json.JSONDecodeError as e:
                last = str(e)
            except httpx.HTTPError as e:
                raise self._network(e)
        raise AIError(f"The AI returned invalid structured data ({last}). Please retry.", 502)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Groq has no embeddings endpoint; RAG embeddings stay local via Ollama (free).
        from app.services.ai.ollama import OllamaProvider
        return await OllamaProvider().embed(texts)

    async def health(self) -> dict:
        info = {"provider": self.name, "reachable": False, "chat_model": self.model,
                "chat_model_available": False, "hint": None}
        if not self.api_key:
            info["hint"] = f"{self.key_env_name} is not set in backend/.env."
            return info
        try:
            async with self._client() as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
        except httpx.HTTPError:
            info["hint"] = f"Can't reach {self.name.capitalize()}. Check your internet connection."
            return info
        if resp.status_code in (401, 403):
            info["hint"] = f"{self.name.capitalize()} rejected the API key. Check {self.key_env_name}."
            return info
        if resp.status_code >= 400:
            info["hint"] = f"{self.name.capitalize()} returned status {resp.status_code}."
            return info
        info["reachable"] = True
        ids = {m.get("id") for m in resp.json().get("data", [])}
        info["chat_model_available"] = self.model in ids
        if not info["chat_model_available"]:
            info["hint"] = f"Model '{self.model}' is not available on your account. Pick one from the {self.name.capitalize()} console."
        return info
