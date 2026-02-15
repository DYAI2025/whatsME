"""QA-Tests fuer den Prosodie-Detektor (prosody.py).

Prueft: Heuristik basierend auf Pausendauer.
Formel: Score = min(1.0, pause_ms / 700.0); Score 0.0 bei pause_ms <= 0
"""

import pytest

from app.core.detectors.prosody import detect_hesitation


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path)
# ---------------------------------------------------------------------------

class TestProsodyDetectorPositive:
    """Korrekte Erkennung bei gueltiger Eingabe."""

    def test_pause_700ms_returns_1(self):
        """Exakt 700ms -> Score 1.0 (Schwellenwert erreicht)."""
        score = detect_hesitation({"pause_ms": 700})
        assert score == pytest.approx(1.0)

    def test_pause_above_700ms_capped_at_1(self):
        """Ueber 700ms -> Score bleibt 1.0 (min-Deckelung)."""
        score = detect_hesitation({"pause_ms": 1500})
        assert score == pytest.approx(1.0)

    def test_pause_350ms_returns_half(self):
        """350ms = 350/700 = 0.5."""
        score = detect_hesitation({"pause_ms": 350})
        assert score == pytest.approx(0.5)

    def test_pause_100ms_returns_fraction(self):
        """100ms -> Score = 100/700 ≈ 0.143."""
        score = detect_hesitation({"pause_ms": 100})
        assert score == pytest.approx(100.0 / 700.0)

    def test_pause_1ms_returns_small_score(self):
        """Minimale positive Pause -> sehr kleiner Score > 0."""
        score = detect_hesitation({"pause_ms": 1})
        assert score > 0.0
        assert score == pytest.approx(1.0 / 700.0)

    def test_pause_750ms_returns_1(self):
        """750ms (Frontend-Default) -> Score 1.0."""
        score = detect_hesitation({"pause_ms": 750})
        assert score == pytest.approx(1.0)

    def test_linear_interpolation(self):
        """Score steigt linear: 200ms < 400ms < 600ms."""
        s200 = detect_hesitation({"pause_ms": 200})
        s400 = detect_hesitation({"pause_ms": 400})
        s600 = detect_hesitation({"pause_ms": 600})
        assert s200 < s400 < s600


# ---------------------------------------------------------------------------
# Negativ-Tests (Falsche/Leere Eingabe -> erwartetes Verhalten)
# ---------------------------------------------------------------------------

class TestProsodyDetectorNegative:
    """Korrektes Verhalten bei ungueltigem oder fehlendem Input."""

    def test_pause_zero_returns_zero(self):
        """pause_ms=0 -> Score 0.0."""
        score = detect_hesitation({"pause_ms": 0})
        assert score == 0.0

    def test_pause_negative_returns_zero(self):
        """Negative Pause -> Score 0.0."""
        score = detect_hesitation({"pause_ms": -100})
        assert score == 0.0

    def test_missing_pause_key_returns_zero(self):
        """'pause_ms' fehlt im Dict -> Score 0.0."""
        score = detect_hesitation({"pitch_slope": -0.1})
        assert score == 0.0

    def test_empty_dict_returns_zero(self):
        """Leeres Dict -> Score 0.0."""
        score = detect_hesitation({})
        assert score == 0.0

    def test_non_dict_input_returns_zero(self):
        """Kein Dict als Eingabe -> Score 0.0 (kein Absturz)."""
        score = detect_hesitation("nicht_ein_dict")
        assert score == 0.0

    def test_none_input_returns_zero(self):
        """None als Eingabe -> Score 0.0 (kein Absturz)."""
        score = detect_hesitation(None)
        assert score == 0.0

    def test_list_input_returns_zero(self):
        """Liste als Eingabe -> Score 0.0 (kein Absturz)."""
        score = detect_hesitation([700])
        assert score == 0.0
