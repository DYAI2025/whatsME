"""Prosody feature detector placeholder."""


def detect_hesitation(prosody: dict) -> float:
    """Heuristic detection for hesitation based on pause duration."""
    pause_ms = prosody.get("pause_ms", 0) if isinstance(prosody, dict) else 0
    if pause_ms <= 0:
        return 0.0
    # Map pauses above 700ms towards a strong hesitation signal.
    return min(1.0, pause_ms / 700.0)
