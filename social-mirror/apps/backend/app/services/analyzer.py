"""Text analyzer service that orchestrates marker detection."""

from collections.abc import Sequence

from ..core.detectors.embedding import detect_semantic_matches
from ..core.detectors.dep import detect_dependency_patterns
from ..core.detectors.prosody import detect_hesitation
from ..core.interpret import interpret_activation
from ..core.registry import DEFAULT_MARKERS, Marker
from ..core.scoring import aggregate_scores
from ..models.schemas import ActivationEvent, Evidence

SEMANTIC_EXEMPLARS: dict[str, Sequence[str]] = {
    "SEM_BOUNDARY_SETTING": (
        "klare grenzen",
        "festlegen",
        "durchsetzen",
    ),
    "MEMA_WITHDRAWAL_SIGNAL": (
        "ich ziehe mich",
        "abstand",
        "zurückziehen",
    ),
    "CLU_TOPIC_BUDGET_TIME": (
        "zeitplan",
        "budget",
        "zeitrahmen",
    ),
}

DEPENDENCY_PATTERNS: dict[str, Sequence[str]] = {
    "SEM_BOUNDARY_SETTING": ("grenzen", "bitte"),
    "MEMA_WITHDRAWAL_SIGNAL": ("ruhe", "allein"),
    "CLU_TOPIC_BUDGET_TIME": ("zeit", "plan"),
}


def _build_evidence(marker: Marker, scores: dict[str, float]) -> list[Evidence]:
    evidence: list[Evidence] = []
    if semantic := scores.get("semantic"):
        evidence.append(
            Evidence(
                type="semantic",
                detail=f"Semantische Beispiele lieferten einen Score von {semantic:.2f}.",
            )
        )
    if dep := scores.get("dependency"):
        evidence.append(
            Evidence(
                type="syntax",
                detail=f"Abhängigkeitsmuster unterstützten den Marker mit {dep:.2f}.",
            )
        )
    if prosody := scores.get("prosody"):
        evidence.append(
            Evidence(
                type="prosody",
                detail=f"Prosodische Hinweise (Pause) ergaben {prosody:.2f}.",
            )
        )
    return evidence


def analyze_text(text: str, lang: str, prosody: dict) -> dict:
    """Return activation events for the configured LeanDeep markers."""
    activations: list[ActivationEvent] = []
    for marker in DEFAULT_MARKERS.all():
        semantic_score = detect_semantic_matches(
            text,
            SEMANTIC_EXEMPLARS.get(marker.code, ()),
        )
        dependency_score = detect_dependency_patterns(
            text.split(),
            DEPENDENCY_PATTERNS.get(marker.code, ()),
        )
        prosody_score = detect_hesitation(prosody) if marker.family == "ATO" else 0.0

        combined_score = aggregate_scores(
            {
                "semantic": semantic_score,
                "dependency": dependency_score,
                "prosody": prosody_score,
            }
        )
        evidence = _build_evidence(
            marker,
            {
                "semantic": semantic_score,
                "dependency": dependency_score,
                "prosody": prosody_score,
            },
        )
        activation = ActivationEvent(
            marker=marker.code,
            family=marker.family,
            score=combined_score,
            uncertainty=max(0.0, 1 - combined_score),
            interpretation=interpret_activation(marker.code, combined_score),
            schema=marker.schema,
            evidence=evidence,
        )
        activations.append(activation)

    return {"lang": lang, "activations": [a.model_dump() for a in activations]}
