"""QA-Tests fuer den syntaktischen Detektor (dep.py).

Prueft: Token-Matching gegen Schluesselwort-Muster.
Formel: Score = Treffer_Tokens / Anzahl_Muster, gedeckelt auf 1.0
"""

import pytest

from app.core.detectors.dep import detect_dependency_patterns


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path)
# ---------------------------------------------------------------------------

class TestDepDetectorPositive:
    """Korrekte Erkennung bei gueltiger Eingabe."""

    def test_all_patterns_match_returns_1(self):
        """Beide SEM-Muster im Token-Set -> Score 1.0."""
        tokens = ["Bitte", "setzen", "wir", "Grenzen"]
        patterns = ("grenzen", "bitte")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == pytest.approx(1.0)

    def test_one_of_two_patterns_match(self):
        """Ein Muster trifft -> Score 0.5."""
        tokens = ["Bitte", "warten", "Sie"]
        patterns = ("bitte", "grenzen")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == pytest.approx(0.5)

    def test_case_insensitive_matching(self):
        """Gross-/Kleinschreibung wird normalisiert."""
        tokens = ["GRENZEN", "BITTE"]
        patterns = ("grenzen", "bitte")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == pytest.approx(1.0)

    def test_mema_patterns_match(self):
        """MEMA-Muster: 'ruhe' und 'allein'."""
        tokens = ["Ich", "brauche", "Ruhe", "und", "bin", "allein"]
        patterns = ("ruhe", "allein")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == pytest.approx(1.0)

    def test_clu_patterns_match(self):
        """CLU-Muster: 'zeit' und 'plan'."""
        tokens = ["Der", "Plan", "kostet", "Zeit"]
        patterns = ("zeit", "plan")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == pytest.approx(1.0)

    def test_single_pattern_single_token(self):
        """Ein Token, ein Muster, beide gleich -> Score 1.0."""
        score = detect_dependency_patterns(["grenzen"], ("grenzen",))
        assert score == pytest.approx(1.0)

    def test_duplicate_tokens_still_one_hit(self):
        """Doppelte Tokens aendern nichts am Treffer (Set-basiert)."""
        tokens = ["grenzen", "grenzen", "grenzen"]
        patterns = ("grenzen",)
        score = detect_dependency_patterns(tokens, patterns)
        assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Negativ-Tests (Falsche/Leere Eingabe -> erwartetes Verhalten)
# ---------------------------------------------------------------------------

class TestDepDetectorNegative:
    """Korrektes Verhalten bei ungueltigem oder irrelevantem Input."""

    def test_empty_tokens_returns_zero(self):
        """Keine Tokens -> Score 0.0."""
        score = detect_dependency_patterns([], ("grenzen",))
        assert score == 0.0

    def test_empty_patterns_returns_zero(self):
        """Keine Muster -> Score 0.0."""
        score = detect_dependency_patterns(["Hallo"], ())
        assert score == 0.0

    def test_both_empty_returns_zero(self):
        """Leere Tokens UND leere Muster -> Score 0.0."""
        score = detect_dependency_patterns([], ())
        assert score == 0.0

    def test_no_pattern_match_returns_zero(self):
        """Kein Muster im Token-Set -> Score 0.0."""
        tokens = ["Wetter", "ist", "schoen"]
        patterns = ("grenzen", "bitte")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == 0.0

    def test_substring_not_counted_as_token(self):
        """'grenz' ist NICHT 'grenzen' (exaktes Token-Matching)."""
        tokens = ["grenz", "bitt"]
        patterns = ("grenzen", "bitte")
        score = detect_dependency_patterns(tokens, patterns)
        assert score == 0.0

    def test_partial_word_in_compound_not_matched(self):
        """'Zeitplan' als ein Token matched nicht auf 'zeit' (kein Substring)."""
        tokens = ["Zeitplan"]
        patterns = ("zeit",)
        score = detect_dependency_patterns(tokens, patterns)
        assert score == 0.0

    def test_score_never_exceeds_one(self):
        """Score bleibt bei 1.0 gedeckelt."""
        tokens = ["grenzen", "bitte", "extra"]
        patterns = ("grenzen",)
        score = detect_dependency_patterns(tokens, patterns)
        assert score <= 1.0
