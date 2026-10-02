from abc import ABC, abstractmethod
from typing import AsyncIterator


class AIError(Exception):
    """Raised for any AI-provider problem. `message` is safe to show to users."""

    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict]) -> str: ...

    @abstractmethod
    def stream(self, messages: list[dict]) -> AsyncIterator[str]: ...

    @abstractmethod
    async def chat_json(self, messages: list[dict], schema: dict | None = None) -> dict: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def health(self) -> dict: ...
