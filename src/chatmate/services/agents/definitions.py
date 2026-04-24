from __future__ import annotations

from chatmate.services.llm.base import ToolDefinition

TOOL_DEFINITIONS: list[ToolDefinition] = [
    ToolDefinition(
        name="get_weather",
        description=(
            "Get a 7-day weather forecast for a location. "
            "Call this whenever the user mentions travelling to or asking about a place."
        ),
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country, e.g. 'Hanoi, Vietnam'",
                },
            },
            "required": ["location"],
        },
    ),
    ToolDefinition(
        name="get_exchange_rates",
        description=(
            "Get live exchange rates from the local currency to GBP, EUR and USD. "
            "Call this when the user asks about money, costs, or currency at a destination."
        ),
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country, e.g. 'Hanoi, Vietnam'",
                },
            },
            "required": ["location"],
        },
    ),
    ToolDefinition(
        name="get_things_to_do",
        description=(
            "Get nearby landmarks and attractions for a location so you can recommend "
            "the top 10 things to do, adjusted for the time of year."
        ),
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country, e.g. 'Hanoi, Vietnam'",
                },
                "month": {
                    "type": "string",
                    "description": "Month of visit for seasonal recommendations, e.g. 'July'",
                },
            },
            "required": ["location"],
        },
    ),
]
