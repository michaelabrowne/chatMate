from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema object


TokenCallback = Callable[[str], None] | None


class LLMClient(ABC):
    @abstractmethod
    def generate(self, messages: list[dict], on_token: TokenCallback = None) -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        tool_executor: Callable[[str, dict], str],
        on_token: TokenCallback = None,
    ) -> str:
        return self.generate(messages, on_token=on_token)
