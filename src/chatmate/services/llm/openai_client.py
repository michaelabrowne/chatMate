from __future__ import annotations

from openai import OpenAI

from chatmate.services.llm.base import LLMClient


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
