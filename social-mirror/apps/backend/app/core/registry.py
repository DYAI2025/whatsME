"""Registry for LeanDeep markers used across the analyzer pipeline."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Marker:
    family: str
    code: str
    schema: str
    description: str


class MarkerRegistry:
    """In-memory registry that exposes marker metadata for downstream use."""

    def __init__(self, markers: Iterable[Marker]):
        self._markers = {marker.code: marker for marker in markers}

    def get(self, code: str) -> Marker | None:
        return self._markers.get(code)

    def all(self) -> list[Marker]:
        return list(self._markers.values())


DEFAULT_MARKERS = MarkerRegistry(
    markers=[
        Marker(
            family="SEM",
            code="SEM_BOUNDARY_SETTING",
            schema="LD-3.5",
            description="Signals boundary setting statements in negotiations.",
        ),
        Marker(
            family="MEMA",
            code="MEMA_WITHDRAWAL_SIGNAL",
            schema="LD-3.5",
            description="Captures withdrawal or distancing language cues.",
        ),
        Marker(
            family="CLU",
            code="CLU_TOPIC_BUDGET_TIME",
            schema="LD-3.5",
            description="Highlights discussion around time budgeting within topics.",
        ),
        Marker(
            family="ATO",
            code="ATO_HESITATION_VOICE",
            schema="LD-3.5",
            description="Indicates hesitation markers from prosodic measurements.",
        ),
    ]
)
