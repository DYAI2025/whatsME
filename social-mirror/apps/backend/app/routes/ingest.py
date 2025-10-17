from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class IngestEvent(BaseModel):
    source: str = Field(..., description="Origin of the ingested payload, e.g. WhatsApp.")
    payload: dict = Field(..., description="Raw event payload as received from collectors.")


@router.post("/events")
def ingest_event(event: IngestEvent) -> dict[str, str]:
    """Placeholder ingestion endpoint for collector integration."""
    # Future implementation will persist events and trigger downstream pipelines.
    return {"status": "accepted", "source": event.source}
