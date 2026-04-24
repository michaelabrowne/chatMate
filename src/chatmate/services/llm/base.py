from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema object


class LLMClient(ABC):
    @abstractmethod
    def generate(self, messages: list[dict]) -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        tool_executor: Callable[[str, dict], str],
    ) -> str:
        # Default fallback — subclasses override for real tool-use support
        return self.generate(messages)
