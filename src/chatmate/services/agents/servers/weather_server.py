from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from chatmate.services.agents.tools.weather import get_weather

app = FastAPI(
    title="Weather Agent",
    description="Returns a 7-day weather forecast for a given location.",
    version="1.0.0",
)


class WeatherRequest(BaseModel):
    location: str = Field(..., description="City and country, e.g. 'Hanoi, Vietnam'")


class AgentResponse(BaseModel):
    result: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/get_weather", operation_id="get_weather", response_model=AgentResponse)
def invoke(req: WeatherRequest) -> AgentResponse:
    return AgentResponse(result=get_weather(req.location))


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8771, log_level="warning")


if __name__ == "__main__":
    main()
