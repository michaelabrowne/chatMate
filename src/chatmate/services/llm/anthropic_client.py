from __future__ import annotations

from anthropic import Anthropic

from chatmate.services.llm.base import LLMClient


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        system_prompt = ""
        prompt_messages: list[dict[str, str]] = []

        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            else:
                prompt_messages.append(message)

        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            max_tokens=1024,
            messages=prompt_messages,
        )
        parts = [block.text for block in response.content if getattr(block, "text", None)]
        return "\n".join(parts)
