from __future__ import annotations

from chatmate.services.agents.definitions import TOOL_DEFINITIONS
from chatmate.services.agents.tools.currency import get_exchange_rates
from chatmate.services.agents.tools.things_to_do import get_things_to_do
from chatmate.services.agents.tools.weather import get_weather
from chatmate.services.llm.base import ToolDefinition

_TOOLS: dict[str, callable] = {
    "get_weather": get_weather,
    "get_exchange_rates": get_exchange_rates,
    "get_things_to_do": get_things_to_do,
}


class ToolDispatcher:
    @property
    def definitions(self) -> list[ToolDefinition]:
        return TOOL_DEFINITIONS

    def execute(self, name: str, arguments: dict) -> str:
        fn = _TOOLS.get(name)
        if fn is None:
            return f"Unknown tool: {name}"
        try:
            return fn(**arguments)
        except Exception as exc:
            return f"Tool {name} failed: {exc}"
