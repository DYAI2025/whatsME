"""Convert scores into human-readable interpretations."""


def interpret_activation(marker_code: str, score: float) -> str:
    """Return a textual interpretation for the activation score."""
    if score >= 0.75:
        return f"{marker_code} ist stark aktiviert."
    if score >= 0.4:
        return f"{marker_code} zeigt moderate Aktivität."
    if score > 0:
        return f"{marker_code} hat nur leichte Hinweise."
    return f"{marker_code} ist derzeit nicht aktiv."
