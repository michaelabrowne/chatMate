from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

from chatmate.services.agents.tools.things_to_do import get_things_to_do

app = FastAPI(
    title="Things To Do Agent",
    description="Returns nearby landmarks and attractions for a location.",
    version="1.0.0",
)


class ThingsToDoRequest(BaseModel):
    location: str = Field(..., description="City and country, e.g. 'Hanoi, Vietnam'")
    month: str = Field("", description="Month of visit for seasonal recommendations, e.g. 'July'")


class AgentResponse(BaseModel):
    result: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/get_things_to_do", operation_id="get_things_to_do", response_model=AgentResponse)
def invoke(req: ThingsToDoRequest) -> AgentResponse:
    return AgentResponse(result=get_things_to_do(req.location, req.month))


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8773, log_level="warning")


if __name__ == "__main__":
    main()
