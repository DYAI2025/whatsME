"""Semantic similarity detector placeholder."""

from typing import Iterable


def detect_semantic_matches(text: str, exemplars: Iterable[str]) -> float:
    """Return a heuristic semantic similarity score between 0 and 1."""
    exemplar_list = list(exemplars)
    if not text or not exemplar_list:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for ex in exemplar_list if ex.lower() in text_lower)
    return min(1.0, hits / len(exemplar_list))
