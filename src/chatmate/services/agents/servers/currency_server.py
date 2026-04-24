from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from chatmate.services.agents.tools.currency import get_exchange_rates

app = FastAPI(
    title="Currency Agent",
    description="Returns live exchange rates for the local currency at a given location.",
    version="1.0.0",
)


class CurrencyRequest(BaseModel):
    location: str = Field(..., description="City and country, e.g. 'Hanoi, Vietnam'")


class AgentResponse(BaseModel):
    result: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/get_exchange_rates", operation_id="get_exchange_rates", response_model=AgentResponse)
def invoke(req: CurrencyRequest) -> AgentResponse:
    return AgentResponse(result=get_exchange_rates(req.location))


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8772, log_level="warning")


if __name__ == "__main__":
    main()
