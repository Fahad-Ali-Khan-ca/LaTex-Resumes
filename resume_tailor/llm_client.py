"""Provider-agnostic LLM client wrapper.

Supports Anthropic and OpenAI out of the box. New providers can be added
by subclassing LLMClient and calling register_provider().
"""

from abc import ABC, abstractmethod
from typing import Optional

from .config import Config


class LLMClient(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a prompt to the LLM and return the response text."""
        ...


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""


# Provider registry
_PROVIDERS: dict[str, type[LLMClient]] = {
    "anthropic": AnthropicClient,
    "openai": OpenAIClient,
}


def create_llm_client(config: Config) -> LLMClient:
    """Factory function to create the appropriate LLM client."""
    provider_cls = _PROVIDERS.get(config.llm_provider.lower())
    if not provider_cls:
        available = ", ".join(_PROVIDERS.keys())
        raise ValueError(
            f"Unknown LLM provider '{config.llm_provider}'. "
            f"Available: {available}"
        )
    return provider_cls(api_key=config.llm_api_key, model=config.llm_model)


def register_provider(name: str, cls: type[LLMClient]) -> None:
    """Register a custom LLM provider."""
    _PROVIDERS[name.lower()] = cls
