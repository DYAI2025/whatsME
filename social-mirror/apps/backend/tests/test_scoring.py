"""QA-Tests fuer die Score-Aggregation (scoring.py).

Prueft: Mittelwertbildung ueber Detektor-Scores, None-Werte werden ignoriert.
Formel: Gesamtscore = Summe(values) / Anzahl(non-None values)
"""

import pytest

from app.core.scoring import aggregate_scores


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path)
# ---------------------------------------------------------------------------

class TestScoringPositive:
    """Korrekte Aggregation bei gueltiger Eingabe."""

    def test_three_equal_scores(self):
        """Drei gleiche Scores -> Mittelwert = gleicher Wert."""
        score = aggregate_scores({"semantic": 0.5, "dependency": 0.5, "prosody": 0.5})
        assert score == pytest.approx(0.5)

    def test_mixed_scores_average(self):
        """Verschiedene Scores -> arithmetischer Mittelwert."""
        score = aggregate_scores({"semantic": 0.6, "dependency": 0.3, "prosody": 0.0})
        assert score == pytest.approx((0.6 + 0.3 + 0.0) / 3.0)

    def test_single_score(self):
        """Ein einziger Score -> Mittelwert = Score selbst."""
        score = aggregate_scores({"semantic": 0.8})
        assert score == pytest.approx(0.8)

    def test_all_ones(self):
        """Alle maximal -> Mittelwert 1.0."""
        score = aggregate_scores({"a": 1.0, "b": 1.0, "c": 1.0})
        assert score == pytest.approx(1.0)

    def test_all_zeros(self):
        """Alle null -> Mittelwert 0.0."""
        score = aggregate_scores({"a": 0.0, "b": 0.0, "c": 0.0})
        assert score == pytest.approx(0.0)

    def test_none_values_ignored(self):
        """None-Werte werden rausgefiltert."""
        score = aggregate_scores({"semantic": 0.6, "dependency": None, "prosody": 0.4})
        assert score == pytest.approx((0.6 + 0.4) / 2.0)

    def test_two_scores_average(self):
        """Zwei Scores: (0.67 + 1.0) / 2 = 0.835."""
        score = aggregate_scores({"semantic": 0.67, "dependency": 1.0})
        assert score == pytest.approx((0.67 + 1.0) / 2.0)

    def test_typical_sem_analysis(self):
        """Typisches SEM-Szenario: Semantik 0.67, Syntax 0.5, Prosodie 0.0."""
        score = aggregate_scores({"semantic": 2/3, "dependency": 0.5, "prosody": 0.0})
        expected = (2/3 + 0.5 + 0.0) / 3.0
        assert score == pytest.approx(expected)

    def test_typical_ato_analysis(self):
        """Typisches ATO-Szenario: Semantik 0.0, Syntax 0.0, Prosodie 1.0."""
        score = aggregate_scores({"semantic": 0.0, "dependency": 0.0, "prosody": 1.0})
        expected = 1.0 / 3.0
        assert score == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Negativ-Tests (Falsche/Leere Eingabe -> erwartetes Verhalten)
# ---------------------------------------------------------------------------

class TestScoringNegative:
    """Korrektes Verhalten bei leerem oder nur-None-Input."""

    def test_empty_signals_returns_zero(self):
        """Leeres Dict -> Score 0.0."""
        score = aggregate_scores({})
        assert score == 0.0

    def test_all_none_returns_zero(self):
        """Alle Werte None -> Score 0.0."""
        score = aggregate_scores({"a": None, "b": None})
        assert score == 0.0
