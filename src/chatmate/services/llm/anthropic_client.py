from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from anthropic import Anthropic

from chatmate.services.llm.base import LLMClient, ToolDefinition, TokenCallback


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(self, messages: list[dict], on_token: TokenCallback = None) -> str:
        system_prompt = ""
        prompt_messages: list[dict] = []
        for message in messages:
            if message["role"] == "system":
                system_prompt = message["content"]
            else:
                prompt_messages.append(message)

        if on_token:
            with self.client.messages.stream(
                model=self.model,
                system=system_prompt,
                max_tokens=1024,
                messages=prompt_messages,
            ) as stream:
                for text in stream.text_stream:
                    on_token(text)
            return stream.get_final_text()

        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            max_tokens=1024,
            messages=prompt_messages,
        )
        return "\n".join(b.text for b in response.content if getattr(b, "text", None))

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        tool_executor: Callable[[str, dict], str],
        on_token: TokenCallback = None,
    ) -> str:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        working = [m for m in messages if m["role"] != "system"]

        anthropic_tools = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in tools
        ]

        for _ in range(10):
            with self.client.messages.stream(
                model=self.model,
                system=system,
                max_tokens=4096,
                tools=anthropic_tools,
                messages=working,
            ) as stream:
                # Stream text tokens for the final (non-tool) turn
                for event in stream:
                    if (
                        event.type == "content_block_delta"
                        and getattr(event.delta, "type", None) == "text_delta"
                        and on_token
                    ):
                        on_token(event.delta.text)

                final_msg = stream.get_final_message()

            assistant_content = []
            for block in final_msg.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append(
                        {"type": "tool_use", "id": block.id, "name": block.name, "input": block.input}
                    )

            if final_msg.stop_reason == "end_turn":
                return "\n".join(b["text"] for b in assistant_content if b.get("type") == "text")

            working.append({"role": "assistant", "content": assistant_content})

            tool_calls = [b for b in final_msg.content if b.type == "tool_use"]
            with ThreadPoolExecutor() as ex:
                futures = {tc.id: ex.submit(tool_executor, tc.name, tc.input) for tc in tool_calls}

            working.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tid, "content": fut.result()}
                    for tid, fut in futures.items()
                ],
            })

        return ""
