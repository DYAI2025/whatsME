"""QA-Tests fuer die menschenlesbare Interpretation (interpret.py).

Prueft: Score-Schwellen und korrekte Textausgabe in Deutsch.
Schwellen: >= 0.75 stark | >= 0.4 moderat | > 0 leicht | == 0 inaktiv
"""

import pytest

from app.core.interpret import interpret_activation


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path) – Korrekte Zuordnung Score -> Text
# ---------------------------------------------------------------------------

class TestInterpretPositive:
    """Korrekte Interpretation bei gueltigem Score."""

    def test_strong_activation_at_075(self):
        """Score exakt 0.75 -> 'stark aktiviert'."""
        result = interpret_activation("SEM_BOUNDARY_SETTING", 0.75)
        assert "stark aktiviert" in result
        assert "SEM_BOUNDARY_SETTING" in result

    def test_strong_activation_above_075(self):
        """Score 0.9 -> 'stark aktiviert'."""
        result = interpret_activation("SEM_BOUNDARY_SETTING", 0.9)
        assert "stark aktiviert" in result

    def test_strong_activation_at_1(self):
        """Score 1.0 -> 'stark aktiviert'."""
        result = interpret_activation("TEST_MARKER", 1.0)
        assert "stark aktiviert" in result

    def test_moderate_activation_at_04(self):
        """Score exakt 0.4 -> 'moderate Aktivität'."""
        result = interpret_activation("MEMA_WITHDRAWAL_SIGNAL", 0.4)
        assert "moderate Aktivität" in result
        assert "MEMA_WITHDRAWAL_SIGNAL" in result

    def test_moderate_activation_at_074(self):
        """Score 0.74 -> noch moderat (unter 0.75)."""
        result = interpret_activation("CLU_TOPIC_BUDGET_TIME", 0.74)
        assert "moderate Aktivität" in result

    def test_light_hint_at_001(self):
        """Score 0.01 -> 'leichte Hinweise'."""
        result = interpret_activation("ATO_HESITATION_VOICE", 0.01)
        assert "leichte Hinweise" in result

    def test_light_hint_at_039(self):
        """Score 0.39 -> noch leicht (unter 0.4)."""
        result = interpret_activation("SEM_BOUNDARY_SETTING", 0.39)
        assert "leichte Hinweise" in result

    def test_inactive_at_zero(self):
        """Score 0.0 -> 'nicht aktiv'."""
        result = interpret_activation("SEM_BOUNDARY_SETTING", 0.0)
        assert "nicht aktiv" in result

    def test_marker_code_in_output(self):
        """Marker-Code erscheint immer im Ausgabetext."""
        for marker in ["SEM_BOUNDARY_SETTING", "MEMA_WITHDRAWAL_SIGNAL",
                        "CLU_TOPIC_BUDGET_TIME", "ATO_HESITATION_VOICE"]:
            result = interpret_activation(marker, 0.5)
            assert marker in result


# ---------------------------------------------------------------------------
# Negativ-Tests (Grenzwerte und Sonderfaelle)
# ---------------------------------------------------------------------------

class TestInterpretNegative:
    """Grenzwerte und exakte Schwellen-Zuordnung."""

    def test_boundary_075_not_moderate(self):
        """Exakt 0.75 ist NICHT moderat, sondern stark."""
        result = interpret_activation("X", 0.75)
        assert "moderate" not in result
        assert "stark" in result

    def test_boundary_04_not_light(self):
        """Exakt 0.4 ist NICHT leicht, sondern moderat."""
        result = interpret_activation("X", 0.4)
        assert "leichte" not in result
        assert "moderate" in result

    def test_boundary_0_not_light(self):
        """Exakt 0.0 ist NICHT leicht, sondern inaktiv."""
        result = interpret_activation("X", 0.0)
        assert "leichte" not in result
        assert "nicht aktiv" in result

    def test_just_below_075(self):
        """Score 0.7499 -> moderat, nicht stark."""
        result = interpret_activation("X", 0.7499)
        assert "moderate" in result

    def test_just_below_04(self):
        """Score 0.3999 -> leicht, nicht moderat."""
        result = interpret_activation("X", 0.3999)
        assert "leichte" in result

    def test_unknown_marker_code_still_works(self):
        """Unbekannter Marker-Code -> Kein Absturz, Code im Text."""
        result = interpret_activation("UNKNOWN_MARKER", 0.5)
        assert "UNKNOWN_MARKER" in result
