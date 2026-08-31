from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from bitecheck_api.restaurants.router import router as restaurant_router


class HealthResponse(BaseModel):
    """Public contract returned by the API health endpoint."""

    status: Literal["ok"] = "ok"
    service: str = "bitecheck-api"


app = FastAPI(
    title="BiteCheck API",
    description="Backend API for the BiteCheck restaurant intelligence platform.",
    version="0.8.0",
)

app.include_router(restaurant_router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """Confirm that the API process can receive and answer requests."""

    return HealthResponse()
