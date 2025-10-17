"""Pydantic models shared across API responses."""

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    type: str = Field(..., description="Evidence modality, e.g. semantic or prosody.")
    detail: str = Field(..., description="Explanation of why the marker fired.")
    span: str | None = Field(default=None, description="Optional text span.")


class ActivationEvent(BaseModel):
    marker: str
    family: str
    score: float
    uncertainty: float
    interpretation: str
    schema: str
    evidence: list[Evidence]
