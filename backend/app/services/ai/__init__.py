from functools import lru_cache

from app.config import settings
from app.services.ai.base import AIError, AIProvider
from app.services.ai.ollama import OllamaProvider
from app.services.ai.openai_compat import OpenAICompatProvider


@lru_cache
def get_ai() -> AIProvider:
    """Single place to choose the provider (AI_PROVIDER in backend/.env)."""
    name = settings.ai_provider.lower()
    if name == "groq":
        return OpenAICompatProvider("groq", settings.groq_base_url, settings.groq_api_key,
                                    settings.groq_model, "GROQ_API_KEY")
    if name == "xai":
        return OpenAICompatProvider("xai", settings.xai_base_url, settings.xai_api_key,
                                    settings.xai_model, "XAI_API_KEY")
    if name == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unknown AI_PROVIDER '{settings.ai_provider}'. Use groq, xai or ollama.")


def _vision_target() -> tuple[str, str, str]:
    """(provider, model, env var that names the model) for image questions."""
    name = (settings.vision_provider or settings.ai_provider).lower()
    if name == "groq":
        return name, settings.groq_vision_model, "GROQ_VISION_MODEL"
    if name == "xai":
        return name, settings.xai_vision_model, "XAI_VISION_MODEL"
    if name == "ollama":
        return name, settings.ollama_vision_model, "OLLAMA_VISION_MODEL"
    raise ValueError(f"Unknown VISION_PROVIDER '{name}'. Use groq, xai or ollama.")


@lru_cache
def get_vision_ai() -> AIProvider:
    """Provider for messages that include an image. Never falls back to a text-only model:
    if no vision model is configured, the student gets a clear setup message instead."""
    name, model, env = _vision_target()
    if not model:
        raise AIError(f"Image questions need a vision model. Set {env} in backend/.env and restart the backend.", 503)
    if name == "groq":
        return OpenAICompatProvider("groq", settings.groq_base_url, settings.groq_api_key, model,
                                    "GROQ_API_KEY", vision=True, model_env_name=env)
    if name == "xai":
        return OpenAICompatProvider("xai", settings.xai_base_url, settings.xai_api_key, model,
                                    "XAI_API_KEY", vision=True, model_env_name=env)
    return OllamaProvider(model=model)


def vision_status() -> dict:
    """Cheap, no-network summary for /api/health."""
    try:
        name, model, env = _vision_target()
    except ValueError as e:
        return {"provider": None, "model": None, "configured": False, "hint": str(e)}
    key = {"groq": settings.groq_api_key, "xai": settings.xai_api_key}.get(name, "ok")
    hint = None
    if not model:
        hint = f"Set {env} in backend/.env to enable image questions."
    elif not key:
        hint = f"{name.upper()}_API_KEY is not set in backend/.env."
    return {"provider": name, "model": model or None, "configured": bool(model and key), "hint": hint}


async def vision_health() -> dict:
    """vision_status() plus a live check that the vision model exists on the provider account."""
    info = vision_status()
    if not info["configured"]:
        return info
    try:
        live = await get_vision_ai().health()
    except Exception:  # health must never break the endpoint
        return info
    info["reachable"] = live.get("reachable")
    info["available"] = live.get("chat_model_available")
    if live.get("hint"):
        info["hint"] = live["hint"]
    return info


__all__ = ["AIError", "AIProvider", "get_ai", "get_vision_ai", "vision_status", "vision_health"]
