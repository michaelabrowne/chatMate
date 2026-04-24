from __future__ import annotations

import json
import urllib.request

from chatmate.services.agents.definitions import TOOL_DEFINITIONS
from chatmate.services.llm.base import ToolDefinition

_TOOL_PORTS: dict[str, int] = {
    "get_weather": 8771,
    "get_exchange_rates": 8772,
    "get_things_to_do": 8773,
}


class ToolDispatcher:
    @property
    def definitions(self) -> list[ToolDefinition]:
        return TOOL_DEFINITIONS

    def execute(self, name: str, arguments: dict) -> str:
        port = _TOOL_PORTS.get(name)
        if port is None:
            return f"Unknown tool: {name}"
        try:
            payload = json.dumps(arguments).encode()
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/{name}",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())["result"]
        except Exception as exc:
            return f"Tool {name} failed: {exc}"
