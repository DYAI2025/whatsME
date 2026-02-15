"""QA-Tests fuer den semantischen Detektor (embedding.py).

Prueft: Substring-Matching gegen Exemplar-Phrasen.
Formel: Score = Treffer / Anzahl_Exemplare, gedeckelt auf 1.0
"""

import pytest

from app.core.detectors.embedding import detect_semantic_matches


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path)
# ---------------------------------------------------------------------------

class TestSemanticDetectorPositive:
    """Korrekte Erkennung bei gueltiger Eingabe."""

    def test_all_exemplars_match_returns_1(self):
        """Alle drei SEM-Exemplare im Text -> Score 1.0."""
        text = "Wir muessen klare grenzen festlegen und durchsetzen."
        exemplars = ("klare grenzen", "festlegen", "durchsetzen")
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(1.0)

    def test_partial_match_returns_fraction(self):
        """Nur ein Exemplar trifft -> Score = 1/3."""
        text = "Ich will das festlegen."
        exemplars = ("klare grenzen", "festlegen", "durchsetzen")
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(1.0 / 3.0)

    def test_two_of_three_match(self):
        """Zwei von drei Exemplaren -> Score = 2/3."""
        text = "Klare Grenzen durchsetzen."
        exemplars = ("klare grenzen", "durchsetzen", "festlegen")
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(2.0 / 3.0)

    def test_case_insensitive_matching(self):
        """Gross-/Kleinschreibung spielt keine Rolle."""
        text = "KLARE GRENZEN setzen"
        exemplars = ("klare grenzen",)
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(1.0)

    def test_exemplar_embedded_in_longer_word(self):
        """Substring-Match: 'zeit' in 'Zeitplan' wird gefunden."""
        text = "Der Zeitplan steht."
        exemplars = ("zeit",)
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(1.0)

    def test_mema_exemplars_detected(self):
        """MEMA-Marker: Rueckzugssignale werden erkannt."""
        text = "Ich ziehe mich zurueck und brauche Abstand."
        exemplars = ("ich ziehe mich", "abstand", "zurückziehen")
        score = detect_semantic_matches(text, exemplars)
        # "ich ziehe mich" und "abstand" treffen, "zurückziehen" nicht (Umlaut)
        assert score == pytest.approx(2.0 / 3.0)

    def test_clu_exemplars_detected(self):
        """CLU-Marker: Zeitplan/Budget-Themen werden erkannt."""
        text = "Der Zeitplan und das Budget muessen stimmen."
        exemplars = ("zeitplan", "budget", "zeitrahmen")
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(2.0 / 3.0)

    def test_single_exemplar_match(self):
        """Ein einziges Exemplar, das trifft -> Score 1.0."""
        text = "Wir muessen das Budget pruefen."
        exemplars = ("budget",)
        score = detect_semantic_matches(text, exemplars)
        assert score == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Negativ-Tests (Falsche/Leere Eingabe -> erwartetes Verhalten)
# ---------------------------------------------------------------------------

class TestSemanticDetectorNegative:
    """Korrektes Verhalten bei ungueltigem oder irrelevantem Input."""

    def test_empty_text_returns_zero(self):
        """Leerer Text -> Score 0.0."""
        score = detect_semantic_matches("", ("klare grenzen",))
        assert score == 0.0

    def test_empty_exemplars_returns_zero(self):
        """Keine Exemplare -> Score 0.0."""
        score = detect_semantic_matches("Hallo Welt", ())
        assert score == 0.0

    def test_both_empty_returns_zero(self):
        """Leerer Text UND leere Exemplare -> Score 0.0."""
        score = detect_semantic_matches("", ())
        assert score == 0.0

    def test_no_match_returns_zero(self):
        """Kein Exemplar im Text vorhanden -> Score 0.0."""
        text = "Das Wetter ist heute schoen."
        exemplars = ("klare grenzen", "festlegen", "durchsetzen")
        score = detect_semantic_matches(text, exemplars)
        assert score == 0.0

    def test_similar_but_different_word_no_match(self):
        """'grenze' ist nicht 'klare grenzen' als Ganzes? Doch, Substring!
        Aber 'grenzenloses' enthaelt 'grenzen' -> pruefe genau."""
        text = "Die Grenze ist klar."
        exemplars = ("klare grenzen",)
        score = detect_semantic_matches(text, exemplars)
        # "klare grenzen" ist NICHT Substring von "Die Grenze ist klar."
        assert score == 0.0

    def test_partial_phrase_no_match(self):
        """Nur halbe Phrase vorhanden -> kein Treffer."""
        text = "Das war sehr klar."
        exemplars = ("klare grenzen",)
        score = detect_semantic_matches(text, exemplars)
        assert score == 0.0

    def test_unrelated_topic_all_markers_zero(self):
        """Voellig themenfremder Text -> kein Marker trifft."""
        text = "Die Katze sitzt auf dem Sofa."
        for exemplars in [
            ("klare grenzen", "festlegen", "durchsetzen"),
            ("ich ziehe mich", "abstand", "zurückziehen"),
            ("zeitplan", "budget", "zeitrahmen"),
        ]:
            score = detect_semantic_matches(text, exemplars)
            assert score == 0.0, f"Falscher Treffer bei Exemplaren {exemplars}"

    def test_score_never_exceeds_one(self):
        """Score ist auf 1.0 gedeckelt, auch bei doppeltem Hit."""
        text = "budget budget budget"
        exemplars = ("budget",)
        score = detect_semantic_matches(text, exemplars)
        assert score <= 1.0


# ---------------------------------------------------------------------------
# Grenzwert-Tests: Minimaler Kontext fuer Semantik-Erkennung
# ---------------------------------------------------------------------------

class TestSemanticBoundaryContext:
    """Wo liegt der Grenzwert? Welcher minimale Kontext wird benoetigt?"""

    def test_exact_exemplar_is_minimum_context(self):
        """Das exakte Exemplar allein reicht als minimaler Kontext."""
        assert detect_semantic_matches("klare grenzen", ("klare grenzen",)) == 1.0

    def test_single_word_exemplar_minimum(self):
        """Ein einzelnes Wort reicht als minimaler Kontext."""
        assert detect_semantic_matches("festlegen", ("festlegen",)) == 1.0

    def test_one_char_less_than_exemplar_fails(self):
        """Ein Zeichen weniger als das Exemplar -> kein Match."""
        assert detect_semantic_matches("klare grenze", ("klare grenzen",)) == 0.0

    def test_exemplar_as_word_within_sentence(self):
        """Exemplar eingebettet in Satz -> Match."""
        assert detect_semantic_matches("Ich will das festlegen.", ("festlegen",)) == 1.0

    def test_multiword_exemplar_split_across_text(self):
        """Exemplar 'klare grenzen': Woerter muessen zusammen stehen."""
        # "klare" und "grenzen" getrennt durch anderes Wort -> kein Substring-Match
        assert detect_semantic_matches("klare neue grenzen", ("klare grenzen",)) == 0.0

    def test_multiword_exemplar_exact_substring(self):
        """'klare grenzen' als exakter Substring -> Match."""
        assert detect_semantic_matches("Ich brauche klare grenzen hier.", ("klare grenzen",)) == 1.0

    def test_threshold_single_of_many_exemplars(self):
        """Bei 3 Exemplaren und 1 Treffer: Score = 0.33 (unter 0.4 moderate Schwelle)."""
        score = detect_semantic_matches("festlegen", ("klare grenzen", "festlegen", "durchsetzen"))
        assert score == pytest.approx(1.0 / 3.0)
        assert score < 0.4  # Unter der Interpretationsschwelle 'moderat'

    def test_threshold_two_of_three_exemplars(self):
        """Bei 3 Exemplaren und 2 Treffern: Score = 0.67 (ueber moderate Schwelle)."""
        score = detect_semantic_matches(
            "Klare grenzen festlegen.",
            ("klare grenzen", "festlegen", "durchsetzen"),
        )
        assert score == pytest.approx(2.0 / 3.0)
        assert score >= 0.4  # Ueber der Interpretationsschwelle 'moderat'

    def test_whitespace_only_text_returns_zero(self):
        """Nur Leerzeichen sind technisch nicht leer, aber enthalten kein Exemplar."""
        score = detect_semantic_matches("   ", ("klare grenzen",))
        assert score == 0.0

    def test_umlaut_sensitivity(self):
        """Umlaute muessen exakt passen: 'zurückziehen' != 'zurueckziehen'."""
        assert detect_semantic_matches("zurueckziehen", ("zurückziehen",)) == 0.0
        assert detect_semantic_matches("zurückziehen", ("zurückziehen",)) == 1.0
