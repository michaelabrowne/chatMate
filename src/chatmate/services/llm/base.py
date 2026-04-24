from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def generate(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError
