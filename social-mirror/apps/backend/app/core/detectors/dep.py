"""Dependency pattern detector placeholder."""

from typing import Iterable


def detect_dependency_patterns(tokens: Iterable[str], patterns: Iterable[str]) -> float:
    """Simplified dependency matching heuristic that counts pattern hits."""
    token_set = {token.lower() for token in tokens}
    pattern_list = list(patterns)
    if not token_set or not pattern_list:
        return 0.0
    hits = sum(1 for pattern in pattern_list if pattern.lower() in token_set)
    return min(1.0, hits / len(pattern_list))
