from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from openai import OpenAI

from chatmate.services.llm.base import LLMClient, ToolDefinition, TokenCallback


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, messages: list[dict], on_token: TokenCallback = None) -> str:
        if on_token:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            text = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    text += delta
                    on_token(delta)
            return text

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
        on_token: TokenCallback = None,
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
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=working,
                tools=openai_tools,
                tool_choice="auto",
                stream=True,
            )

            accumulated_text = ""
            tool_calls_acc: dict[int, dict] = {}
            finish_reason = None

            for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                finish_reason = choice.finish_reason or finish_reason
                delta = choice.delta

                if delta.content:
                    accumulated_text += delta.content
                    if on_token:
                        on_token(delta.content)

                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc_delta.id:
                            tool_calls_acc[idx]["id"] += tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_acc[idx]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_acc[idx]["arguments"] += tc_delta.function.arguments

            if finish_reason != "tool_calls" or not tool_calls_acc:
                return accumulated_text

            tool_calls = list(tool_calls_acc.values())

            working.append({
                "role": "assistant",
                "content": accumulated_text or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls
                ],
            })

            with ThreadPoolExecutor() as ex:
                futures = {
                    tc["id"]: ex.submit(tool_executor, tc["name"], json.loads(tc["arguments"]))
                    for tc in tool_calls
                }

            for tc in tool_calls:
                working.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": futures[tc["id"]].result(),
                })

        return accumulated_text
