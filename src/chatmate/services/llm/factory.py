from __future__ import annotations

from chatmate.config import AppConfig
from chatmate.services.llm.anthropic_client import AnthropicLLMClient
from chatmate.services.llm.openai_client import OpenAICompatibleLLMClient

_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def build_llm_client(config: AppConfig, provider_name: str | None = None, model_override: str | None = None):
    active = (provider_name or config.provider.active).lower()

    if active == "openai":
        settings = config.provider.openai
        if not settings.api_key:
            raise ValueError("Missing OPENAI_API_KEY in .env for the OpenAI provider.")
        return OpenAICompatibleLLMClient(
            api_key=settings.api_key,
            model=settings.model,
            base_url=settings.base_url,
        )

    if active == "anthropic":
        settings = config.provider.anthropic
        if not settings.api_key:
            raise ValueError("Missing ANTHROPIC_API_KEY in .env for the Anthropic provider.")
        return AnthropicLLMClient(
            api_key=settings.api_key,
            model=settings.model,
        )

    if active == "lmstudio":
        settings = config.provider.lmstudio
        model = model_override or (settings.models[0] if settings.models else "")
        return OpenAICompatibleLLMClient(
            api_key=settings.api_key,
            model=model,
            base_url=settings.base_url,
        )

    if active == "gemini":
        settings = config.provider.gemini
        if not settings.api_key:
            raise ValueError("Missing GEMINI_API_KEY in .env for the Gemini provider.")
        return OpenAICompatibleLLMClient(
            api_key=settings.api_key,
            model=settings.model,
            base_url=_GEMINI_BASE_URL,
        )

    raise ValueError(f"Unsupported provider: {active}")
