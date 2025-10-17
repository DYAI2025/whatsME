from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.analyzer import analyze_text

router = APIRouter()


class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="Input utterance or transcript snippet.")
    lang: str = Field("de", description="Language code for downstream processing.")
    prosody: dict | None = Field(
        default=None,
        description="Optional prosodic measurements such as pause durations.",
    )


@router.post("/text")
def analyze_text_endpoint(payload: AnalyzeRequest) -> dict:
    """Analyze a piece of text and return activation events."""
    return analyze_text(
        text=payload.text,
        lang=payload.lang,
        prosody=payload.prosody or {},
    )
