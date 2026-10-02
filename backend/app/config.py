import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # --- AI Provider -------------------------------------------------------------------------
    ai_provider: str = "groq"  # groq | xai | ollama
    ai_temperature: float = 0.4
    ai_timeout_seconds: float = 60.0
    ai_reasoning_effort: str = "low"  # only used by openai/gpt-oss-* models ("" to disable)

    # --- Groq --------------------------------------------------------------------------------
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"

    # --- xAI ---------------------------------------------------------------------------------
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-4.7"

    # --- Ollama -------------------------------------------------------------------------------
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_embed_model: str = "bge-m3"
    ollama_timeout_seconds: float = 120.0
    ollama_temperature: float = 0.4
    ollama_repeat_penalty: float = 1.1

    # --- Image understanding (vision) --------------------------------------------------------
    # Text chat keeps using AI_PROVIDER/GROQ_MODEL etc.
    # Messages that carry an image go to a vision-capable model instead.
    vision_provider: str = ""  # "" = same provider as AI_PROVIDER; groq | xai | ollama

    groq_vision_model: str = "qwen/qwen3.8-27b"
    xai_vision_model: str = ""  # set to a Grok model that accepts images
    ollama_vision_model: str = ""  # e.g. qwen2.5vl:7b or llava

    max_image_mb: float = 4.0
    upload_dir: str = "./uploads"

    # --- Documents + RAG ---------------------------------------------------------------------
    max_doc_mb: float = 25.0
    rag_top_k: int = 6
    rag_min_score: float = 0.30

    # --- Orin Code: code execution -----------------------------------------------------------
    #
    # Docker is the recommended production runner.
    #
    # For local development without Docker:
    #   CODE_RUNNER=subprocess
    #   CODE_ALLOW_UNSAFE_LOCAL=1
    #
    # Local subprocess execution is NOT a secure sandbox and must not
    # be exposed to untrusted/public users.
    code_runner: str = "docker"
    code_allow_unsafe_local: bool = False

    code_docker_image: str = "python:3.12-slim"

    # Maximum execution time per coding execution request.
    code_time_limit_seconds: float = 2.0

    # Docker memory limit in MB.
    code_memory_mb: int = 128

    # Maximum number of coding executions running simultaneously.
    code_max_concurrent: int = 2

    # --- Database ----------------------------------------------------------------------------
    database_url: str = "sqlite:///./orin.db"

    # --- Authentication ----------------------------------------------------------------------
    jwt_secret: str = "dev-secret-change-me"
    jwt_expire_minutes: int = 1440

    # --- CORS --------------------------------------------------------------------------------
    cors_origins: str = "http://localhost:5173"


settings = Settings()