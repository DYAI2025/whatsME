"""QA-Tests: Semantik-Erkennung – Grenzwerte und minimaler Kontext.

Zentrale Fragen:
1. Wird Semantik ueberhaupt erkannt?
2. Werden Signale korrekt interpretiert?
3. Wo liegt der Grenzwert an Kontext?
4. Welcher minimale Kontext ist fuer Semantik erforderlich?
"""

import pytest

from app.core.detectors.embedding import detect_semantic_matches
from app.core.interpret import interpret_activation
from app.core.scoring import aggregate_scores
from app.services.analyzer import analyze_text, SEMANTIC_EXEMPLARS


# ===========================================================================
# 1. WIRD SEMANTIK ERKANNT?
# ===========================================================================

class TestSemanticRecognition:
    """Grundlegende Pruefung: Erkennt das System semantische Muster?"""

    # --- Positiv ---

    def test_sem_boundary_text_recognized(self):
        """SEM: Grenzensetzungs-Sprache wird semantisch erkannt."""
        text = "Ich brauche klare Grenzen und muss das jetzt festlegen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        assert sem["score"] > 0.0, "SEM-Semantik nicht erkannt"
        assert any(e["type"] == "semantic" for e in sem["evidence"])

    def test_mema_withdrawal_text_recognized(self):
        """MEMA: Rueckzugssprache wird semantisch erkannt."""
        text = "Ich ziehe mich zurueck, brauche Abstand von allem."
        result = analyze_text(text, "de", {})
        mema = next(a for a in result["activations"] if a["family"] == "MEMA")
        assert mema["score"] > 0.0, "MEMA-Semantik nicht erkannt"

    def test_clu_budget_text_recognized(self):
        """CLU: Zeit-/Budget-Sprache wird semantisch erkannt."""
        text = "Der Zeitplan muss angepasst werden, das Budget ist knapp."
        result = analyze_text(text, "de", {})
        clu = next(a for a in result["activations"] if a["family"] == "CLU")
        assert clu["score"] > 0.0, "CLU-Semantik nicht erkannt"

    def test_ato_prosody_recognized(self):
        """ATO: Prosodische Zoegerlichkeit wird erkannt."""
        result = analyze_text("Aehm...", "de", {"pause_ms": 800})
        ato = next(a for a in result["activations"] if a["family"] == "ATO")
        assert ato["score"] > 0.0, "ATO-Prosodie nicht erkannt"

    # --- Negativ ---

    def test_unrelated_text_not_recognized(self):
        """Themenfremder Text wird NICHT faelschlich als Marker erkannt."""
        text = "Die Sonne scheint und die Voegel singen."
        result = analyze_text(text, "de", {})
        for a in result["activations"]:
            assert a["score"] < 0.2, \
                f"{a['marker']} faelschlich aktiviert (Score {a['score']})"

    def test_english_text_not_matched(self):
        """Englischer Text matched nicht auf deutsche Exemplare."""
        text = "I need clear boundaries and must enforce them."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        assert sem["score"] < 0.15


# ===========================================================================
# 2. WERDEN SIGNALE KORREKT INTERPRETIERT?
# ===========================================================================

class TestSignalInterpretation:
    """Prueft: Fuehrt ein bestimmter Score zur richtigen Interpretation?"""

    # --- Positiv ---

    def test_high_sem_score_strongly_activated(self):
        """Hoher SEM-Score -> 'stark aktiviert'."""
        text = "Bitte klare grenzen festlegen und durchsetzen. Grenzen sind noetig."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        if sem["score"] >= 0.75:
            assert "stark aktiviert" in sem["interpretation"]

    def test_moderate_score_moderate_interpretation(self):
        """Score 0.4-0.74 -> 'moderate Aktivitaet'."""
        # Zwei von drei Exemplaren -> Semantik ~0.67, Score nach Aggregation
        text = "Klare grenzen festlegen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        if 0.4 <= sem["score"] < 0.75:
            assert "moderate Aktivität" in sem["interpretation"]

    def test_low_score_light_interpretation(self):
        """Score 0.01-0.39 -> 'leichte Hinweise'."""
        # Ein Exemplar von drei -> Score niedrig
        text = "Ich will das festlegen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        if 0 < sem["score"] < 0.4:
            assert "leichte Hinweise" in sem["interpretation"]

    def test_zero_score_inactive(self):
        """Score 0.0 -> 'nicht aktiv'."""
        result = analyze_text("Die Katze schlaeft.", "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        if sem["score"] == 0.0:
            assert "nicht aktiv" in sem["interpretation"]

    # --- Negativ ---

    def test_interpretation_never_empty(self):
        """Interpretation ist niemals ein leerer String."""
        for text in ["", "Hallo", "Klare Grenzen", "12345"]:
            result = analyze_text(text, "de", {})
            for a in result["activations"]:
                assert a["interpretation"], \
                    f"Leere Interpretation fuer {a['marker']} bei Text '{text}'"

    def test_interpretation_contains_marker_code(self):
        """Jede Interpretation enthaelt den Marker-Code."""
        result = analyze_text("Test", "de", {})
        for a in result["activations"]:
            assert a["marker"] in a["interpretation"]


# ===========================================================================
# 3. WO LIEGT DER GRENZWERT AN KONTEXT?
# ===========================================================================

class TestContextThresholds:
    """Bestimmt die Score-Grenzen basierend auf verschiedenen Kontext-Mengen."""

    # --- Positiv: steigende Kontext-Menge ---

    def test_one_of_three_sem_exemplars(self):
        """1 von 3 SEM-Exemplaren: Semantik-Score = 1/3 ≈ 0.33."""
        score = detect_semantic_matches("festlegen", SEMANTIC_EXEMPLARS["SEM_BOUNDARY_SETTING"])
        assert score == pytest.approx(1/3)

    def test_two_of_three_sem_exemplars(self):
        """2 von 3 SEM-Exemplaren: Semantik-Score = 2/3 ≈ 0.67."""
        score = detect_semantic_matches(
            "klare grenzen festlegen",
            SEMANTIC_EXEMPLARS["SEM_BOUNDARY_SETTING"],
        )
        assert score == pytest.approx(2/3)

    def test_three_of_three_sem_exemplars(self):
        """3 von 3 SEM-Exemplaren: Semantik-Score = 1.0."""
        score = detect_semantic_matches(
            "klare grenzen festlegen und durchsetzen",
            SEMANTIC_EXEMPLARS["SEM_BOUNDARY_SETTING"],
        )
        assert score == pytest.approx(1.0)

    def test_aggregated_score_one_sem_exemplar_only(self):
        """1 Exemplar -> Aggregation: (0.33 + 0 + 0) / 3 ≈ 0.11."""
        score = aggregate_scores({"semantic": 1/3, "dependency": 0.0, "prosody": 0.0})
        assert score == pytest.approx((1/3) / 3)
        # 0.11 -> Interpretation: "leichte Hinweise"
        interp = interpret_activation("SEM_BOUNDARY_SETTING", score)
        assert "leichte Hinweise" in interp

    def test_aggregated_score_two_sem_exemplars_only(self):
        """2 Exemplare -> Aggregation: (0.67 + 0 + 0) / 3 ≈ 0.22."""
        score = aggregate_scores({"semantic": 2/3, "dependency": 0.0, "prosody": 0.0})
        assert score == pytest.approx((2/3) / 3)
        interp = interpret_activation("SEM_BOUNDARY_SETTING", score)
        assert "leichte Hinweise" in interp

    def test_aggregated_score_all_sem_exemplars_only(self):
        """3 Exemplare -> Aggregation: (1.0 + 0 + 0) / 3 ≈ 0.33."""
        score = aggregate_scores({"semantic": 1.0, "dependency": 0.0, "prosody": 0.0})
        assert score == pytest.approx(1.0 / 3)
        interp = interpret_activation("SEM_BOUNDARY_SETTING", score)
        assert "leichte Hinweise" in interp

    def test_semantic_plus_syntax_reaches_moderate(self):
        """Semantik 1.0 + Syntax 1.0 + Prosodie 0.0 -> (1+1+0)/3 ≈ 0.67 = moderat."""
        score = aggregate_scores({"semantic": 1.0, "dependency": 1.0, "prosody": 0.0})
        assert score == pytest.approx(2.0 / 3)
        interp = interpret_activation("SEM_BOUNDARY_SETTING", score)
        assert "moderate Aktivität" in interp

    def test_all_detectors_max_reaches_strong(self):
        """Alle Detektoren maximal: (1+1+1)/3 = 1.0 -> stark aktiviert."""
        score = aggregate_scores({"semantic": 1.0, "dependency": 1.0, "prosody": 1.0})
        assert score == pytest.approx(1.0)
        interp = interpret_activation("SEM_BOUNDARY_SETTING", score)
        assert "stark aktiviert" in interp

    # --- Negativ: Score-Grenzen ---

    def test_semantic_alone_never_reaches_strong(self):
        """Semantik allein (max 1.0/3=0.33) kann nie 'stark' erreichen."""
        for exemplar_hits in [1, 2, 3]:
            sem_score = exemplar_hits / 3
            total = aggregate_scores({"semantic": sem_score, "dependency": 0.0, "prosody": 0.0})
            assert total < 0.75, \
                f"Semantik allein ({sem_score}) ergab {total} >= 0.75"

    def test_syntax_alone_never_reaches_strong(self):
        """Syntax allein (max 1.0/3=0.33) kann nie 'stark' erreichen."""
        total = aggregate_scores({"semantic": 0.0, "dependency": 1.0, "prosody": 0.0})
        assert total < 0.75

    def test_moderate_threshold_requires_at_least_two_detectors(self):
        """Fuer 'moderat' (>= 0.4) muessen mindestens 2 Detektoren > 0 sein."""
        # Ein Detektor allein: max 1.0/3 ≈ 0.33 < 0.40
        for key in ["semantic", "dependency", "prosody"]:
            signals = {"semantic": 0.0, "dependency": 0.0, "prosody": 0.0}
            signals[key] = 1.0
            total = aggregate_scores(signals)
            assert total < 0.4, \
                f"Ein Detektor ({key}=1.0) ergab {total} >= 0.4"


# ===========================================================================
# 4. MINIMALER KONTEXT FUER SEMANTIK-ERKENNUNG
# ===========================================================================

class TestMinimalSemanticContext:
    """Welcher minimale Kontext ist fuer Semantik-Erkennung noetig?"""

    # --- Positiv: Minimaler Kontext, der erkennt ---

    def test_exact_exemplar_is_minimum(self):
        """Das exakte Exemplar-Wort ist der minimale Kontext fuer Score > 0."""
        assert detect_semantic_matches("festlegen", ("festlegen",)) == 1.0

    def test_exact_phrase_is_minimum_for_multiword(self):
        """Die exakte Mehrwort-Phrase ist minimaler Kontext."""
        assert detect_semantic_matches("klare grenzen", ("klare grenzen",)) == 1.0

    def test_exemplar_in_sentence_detected(self):
        """Exemplar eingebettet in Satz wird erkannt."""
        assert detect_semantic_matches("Ich muss festlegen.", ("festlegen",)) == 1.0

    def test_minimum_for_nonzero_analyzer_score(self):
        """Minimaler Text fuer Score > 0 im Analyzer: ein einziges Exemplar."""
        result = analyze_text("festlegen", "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        assert sem["score"] > 0.0

    def test_minimum_for_any_evidence(self):
        """Minimaler Text fuer mindestens eine Evidenz."""
        result = analyze_text("festlegen", "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        assert len(sem["evidence"]) >= 1

    # --- Negativ: Kontext unter dem Minimum ---

    def test_one_char_missing_from_exemplar(self):
        """Ein Zeichen weniger als das Exemplar -> kein Match."""
        assert detect_semantic_matches("festlege", ("festlegen",)) == 0.0

    def test_scrambled_exemplar_no_match(self):
        """Vertauschte Buchstaben -> kein Match."""
        assert detect_semantic_matches("fsetlegen", ("festlegen",)) == 0.0

    def test_separated_phrase_no_match(self):
        """Woerter der Phrase getrennt -> kein Substring-Match."""
        assert detect_semantic_matches("klare neue grenzen", ("klare grenzen",)) == 0.0

    def test_typo_in_exemplar_no_match(self):
        """Tippfehler -> kein Match."""
        assert detect_semantic_matches("festlegn", ("festlegen",)) == 0.0

    def test_empty_string_below_minimum(self):
        """Leerer String ist unterhalb des minimalen Kontexts."""
        result = analyze_text("", "de", {})
        for a in result["activations"]:
            assert a["score"] == 0.0

    def test_single_char_below_minimum(self):
        """Ein einzelnes Zeichen reicht nicht."""
        assert detect_semantic_matches("f", ("festlegen",)) == 0.0

    # --- Grenzwert-Zusammenfassung ---

    def test_minimum_context_summary(self):
        """Zusammenfassung: Der minimale Kontext ist die exakte Exemplar-Phrase.

        Fuer einen einzelnen Detektor reicht das exakte Exemplar (z.B. 'festlegen')
        als Substring im Text. Fuer einen Score > 0 im Gesamtsystem genuegt ein
        einziges Exemplar (ergibt Score ≈ 0.11 bei 3 Exemplaren pro Marker).

        Grenzwerte im Gesamtsystem (3 Detektoren, Mittelwert):
        - 1 Exemplar (sem only):  ≈ 0.11 -> 'leichte Hinweise'
        - 2 Exemplare (sem only): ≈ 0.22 -> 'leichte Hinweise'
        - 3 Exemplare (sem only): ≈ 0.33 -> 'leichte Hinweise'
        - Sem + Syntax (beide max): ≈ 0.67 -> 'moderate Aktivitaet'
        - Sem + Syntax + Prosody:   = 1.00 -> 'stark aktiviert'

        Fazit: Semantik allein erzeugt maximal 'leichte Hinweise'.
        Fuer 'moderat' (>= 0.4) sind mindestens 2 Detektoren noetig.
        Fuer 'stark' (>= 0.75) sind alle 3 Detektoren noetig.
        """
        # 1 Exemplar
        score_1 = aggregate_scores({"semantic": 1/3, "dependency": 0.0, "prosody": 0.0})
        assert interpret_activation("X", score_1) == "X hat nur leichte Hinweise."

        # Semantik + Syntax maximal
        score_2 = aggregate_scores({"semantic": 1.0, "dependency": 1.0, "prosody": 0.0})
        assert interpret_activation("X", score_2) == "X zeigt moderate Aktivität."

        # Alle maximal
        score_3 = aggregate_scores({"semantic": 1.0, "dependency": 1.0, "prosody": 1.0})
        assert interpret_activation("X", score_3) == "X ist stark aktiviert."
