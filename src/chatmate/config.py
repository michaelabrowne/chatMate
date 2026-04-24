from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
import yaml


@dataclass(slots=True)
class AppSettings:
    name: str
    system_prompt: str


@dataclass(slots=True)
class OpenAISettings:
    api_key: str
    model: str
    base_url: str | None = None


@dataclass(slots=True)
class AnthropicSettings:
    api_key: str | None
    model: str


@dataclass(slots=True)
class ProviderSettings:
    active: str
    openai: OpenAISettings
    anthropic: AnthropicSettings
    lmstudio: OpenAISettings


@dataclass(slots=True)
class SearchAgentSettings:
    default_root: str = "."
    default_file_type: str = "pdf"
    case_sensitive: bool = False


@dataclass(slots=True)
class AgentSettings:
    search: SearchAgentSettings


@dataclass(slots=True)
class AppConfig:
    app: AppSettings
    provider: ProviderSettings
    agent: AgentSettings


def _require(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required config key: {key}")
    return mapping[key]


def load_app_config(path: Path) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    load_dotenv(path.parent / ".env")
    raw = yaml.safe_load(path.read_text()) or {}

    app_raw = _require(raw, "app")
    provider_raw = _require(raw, "provider")
    agent_raw = raw.get("agent", {})
    search_raw = agent_raw.get("search", {})

    app = AppSettings(
        name=_require(app_raw, "name"),
        system_prompt=_require(app_raw, "system_prompt"),
    )

    openai_settings = OpenAISettings(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=_require(_require(provider_raw, "openai"), "model"),
        base_url=_require(provider_raw, "openai").get("base_url"),
    )
    anthropic_settings = AnthropicSettings(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model=_require(_require(provider_raw, "anthropic"), "model"),
    )
    lmstudio_settings = OpenAISettings(
        api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
        model=_require(_require(provider_raw, "lmstudio"), "model"),
        base_url=_require(_require(provider_raw, "lmstudio"), "base_url"),
    )

    provider = ProviderSettings(
        active=_require(provider_raw, "active"),
        openai=openai_settings,
        anthropic=anthropic_settings,
        lmstudio=lmstudio_settings,
    )

    agent = AgentSettings(
        search=SearchAgentSettings(
            default_root=search_raw.get("default_root", "."),
            default_file_type=search_raw.get("default_file_type", "pdf"),
            case_sensitive=search_raw.get("case_sensitive", False),
        )
    )

    return AppConfig(app=app, provider=provider, agent=agent)
