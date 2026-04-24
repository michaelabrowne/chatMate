from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from openai import OpenAI

from chatmate.services.llm.base import LLMClient, ToolDefinition


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[ToolDefinition],
        tool_executor: Callable[[str, dict], str],
    ) -> str:
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
        working = list(messages)

        for _ in range(10):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=working,
                tools=openai_tools,
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            # Add assistant turn with tool call requests
            working.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            # Execute all tool calls in parallel, then append individual results
            with ThreadPoolExecutor() as ex:
                futures = {
                    tc.id: ex.submit(
                        tool_executor, tc.function.name, json.loads(tc.function.arguments)
                    )
                    for tc in msg.tool_calls
                }

            for tc in msg.tool_calls:
                working.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": futures[tc.id].result(),
                })

        return ""
