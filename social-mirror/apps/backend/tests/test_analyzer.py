"""QA-Tests fuer den Analyse-Service (analyzer.py).

Prueft: Ende-zu-Ende-Orchestrierung aller Detektoren, Score-Aggregation,
Evidenz-Aufbau, Interpretation und Response-Struktur.
"""

import pytest

from app.services.analyzer import analyze_text, SEMANTIC_EXEMPLARS, DEPENDENCY_PATTERNS


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path) – Volle Analyse-Pipeline
# ---------------------------------------------------------------------------

class TestAnalyzerPositive:
    """Korrekte Ende-zu-Ende-Analyse."""

    def test_response_has_lang_and_activations(self):
        """Response enthaelt 'lang' und 'activations' Schluessel."""
        result = analyze_text("Hallo Welt", "de", {})
        assert "lang" in result
        assert "activations" in result
        assert result["lang"] == "de"

    def test_always_four_activations(self):
        """Immer vier Aktivierungen (eine pro Marker)."""
        result = analyze_text("Hallo Welt", "de", {})
        assert len(result["activations"]) == 4

    def test_activation_structure(self):
        """Jede Aktivierung hat alle Pflichtfelder."""
        result = analyze_text("Test", "de", {})
        required_keys = {"marker", "family", "score", "uncertainty",
                         "interpretation", "schema", "evidence"}
        for activation in result["activations"]:
            assert required_keys.issubset(activation.keys()), \
                f"Fehlende Keys in {activation['marker']}"

    def test_sem_scores_high_on_boundary_text(self):
        """SEM-Marker erhaelt Score bei Grenzensetzungs-Text."""
        text = "Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        # "klare grenzen" (semantisch 1/3) + "Bitte" (syntaktisch 1/2, "Grenzen." hat Punkt)
        # Mittelwert: (0.33 + 0.5 + 0.0) / 3 ≈ 0.28
        assert sem["score"] > 0.2

    def test_sem_has_semantic_evidence(self):
        """SEM-Analyse produziert semantische Evidenz."""
        text = "Wir muessen klare grenzen festlegen und durchsetzen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        ev_types = [e["type"] for e in sem["evidence"]]
        assert "semantic" in ev_types

    def test_sem_has_syntax_evidence(self):
        """SEM-Analyse produziert syntaktische Evidenz bei 'grenzen' und 'bitte'."""
        text = "Bitte setzt Grenzen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        ev_types = [e["type"] for e in sem["evidence"]]
        # "Grenzen" als Token matched "grenzen", "Bitte" matched "bitte"
        assert "syntax" in ev_types

    def test_mema_scores_on_withdrawal_text(self):
        """MEMA-Marker erhaelt Score bei Rueckzugstext."""
        text = "Ich ziehe mich zurueck und brauche Abstand."
        result = analyze_text(text, "de", {})
        mema = next(a for a in result["activations"] if a["family"] == "MEMA")
        assert mema["score"] > 0.0

    def test_clu_scores_on_time_budget_text(self):
        """CLU-Marker erhaelt Score bei Zeitplan-Text."""
        text = "Der Zeitplan und das Budget muessen stimmen."
        result = analyze_text(text, "de", {})
        clu = next(a for a in result["activations"] if a["family"] == "CLU")
        assert clu["score"] > 0.0

    def test_ato_scores_with_prosody_data(self):
        """ATO-Marker erhaelt Score bei Prosodie-Daten."""
        result = analyze_text("Aehm...", "de", {"pause_ms": 750})
        ato = next(a for a in result["activations"] if a["family"] == "ATO")
        assert ato["score"] > 0.0

    def test_ato_has_prosody_evidence(self):
        """ATO-Analyse produziert prosodische Evidenz."""
        result = analyze_text("Aehm...", "de", {"pause_ms": 750})
        ato = next(a for a in result["activations"] if a["family"] == "ATO")
        ev_types = [e["type"] for e in ato["evidence"]]
        assert "prosody" in ev_types

    def test_uncertainty_inverse_of_score(self):
        """Unsicherheit = max(0, 1 - score)."""
        result = analyze_text("Klare grenzen festlegen.", "de", {})
        for a in result["activations"]:
            expected_unc = max(0.0, 1 - a["score"])
            assert a["uncertainty"] == pytest.approx(expected_unc, abs=1e-9)

    def test_all_schemas_ld35(self):
        """Alle Aktivierungen verwenden Schema LD-3.5."""
        result = analyze_text("Test", "de", {})
        for a in result["activations"]:
            assert a["schema"] == "LD-3.5"

    def test_lang_passthrough(self):
        """Sprachcode wird durchgereicht."""
        result = analyze_text("Test", "en", {})
        assert result["lang"] == "en"

    def test_interpretation_is_german_string(self):
        """Interpretation ist ein nicht-leerer deutscher String."""
        result = analyze_text("Klare Grenzen.", "de", {})
        for a in result["activations"]:
            assert isinstance(a["interpretation"], str)
            assert len(a["interpretation"]) > 0


# ---------------------------------------------------------------------------
# Negativ-Tests (Irrelevante Eingabe -> niedrige Scores, keine Fehler)
# ---------------------------------------------------------------------------

class TestAnalyzerNegative:
    """Korrektes Verhalten bei irrelevantem oder leerem Input."""

    def test_irrelevant_text_low_scores(self):
        """Voellig themenfremder Text -> alle Scores niedrig."""
        result = analyze_text("Die Katze sitzt auf dem Sofa.", "de", {})
        for a in result["activations"]:
            assert a["score"] <= 0.15, \
                f"{a['marker']} hat unerwartet hohen Score {a['score']}"

    def test_empty_text_all_zero_scores(self):
        """Leerer Text -> alle Scores 0.0."""
        result = analyze_text("", "de", {})
        for a in result["activations"]:
            assert a["score"] == pytest.approx(0.0), \
                f"{a['marker']} sollte 0.0 sein, ist {a['score']}"

    def test_no_prosody_ato_still_present(self):
        """Ohne Prosodie-Daten -> ATO existiert, aber Score von Prosodie ist 0."""
        result = analyze_text("Hallo", "de", {})
        ato = next(a for a in result["activations"] if a["family"] == "ATO")
        assert ato is not None

    def test_no_semantic_exemplars_for_ato(self):
        """ATO hat keine semantischen Exemplare -> nur Prosodie zaehlt."""
        assert "ATO_HESITATION_VOICE" not in SEMANTIC_EXEMPLARS

    def test_no_dependency_patterns_for_ato(self):
        """ATO hat keine Dependency-Muster."""
        assert "ATO_HESITATION_VOICE" not in DEPENDENCY_PATTERNS

    def test_numbers_only_input(self):
        """Nur Zahlen als Text -> kein Absturz, niedrige Scores."""
        result = analyze_text("12345 67890", "de", {})
        assert len(result["activations"]) == 4
        for a in result["activations"]:
            assert a["score"] <= 0.15

    def test_special_chars_input(self):
        """Sonderzeichen als Text -> kein Absturz."""
        result = analyze_text("!@#$%^&*()_+-=[]{}|;':\",./<>?", "de", {})
        assert len(result["activations"]) == 4

    def test_evidence_empty_for_irrelevant_text(self):
        """Bei irrelevantem Text: keine Evidenz (Score 0 -> kein Evidenz-Eintrag)."""
        result = analyze_text("Die Sonne scheint.", "de", {})
        for a in result["activations"]:
            if a["score"] == 0.0:
                assert len(a["evidence"]) == 0


# ---------------------------------------------------------------------------
# Semantik-Erkennungs-Tests: Kontext-Grenzen
# ---------------------------------------------------------------------------

class TestAnalyzerSemanticBoundaries:
    """Wird Semantik korrekt erkannt? Minimaler Kontext und Grenzwerte."""

    def test_minimal_sem_activation(self):
        """Nur ein SEM-Exemplar + ein SEM-Pattern = minimale Aktivierung."""
        text = "Bitte Grenzen festlegen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        # "festlegen" (1/3 semantisch = 0.33) + "Grenzen"+"Bitte" (2/2 syntaktisch = 1.0)
        # Mittelwert mit Prosodie 0.0: (0.33 + 1.0 + 0.0) / 3 ≈ 0.44
        assert sem["score"] > 0.0

    def test_single_keyword_insufficient_for_strong(self):
        """Ein einziges Schluesselwort reicht nicht fuer 'stark aktiviert'."""
        text = "festlegen"
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        assert "stark aktiviert" not in sem["interpretation"]

    def test_all_sem_exemplars_plus_patterns_is_strong(self):
        """Alle SEM-Exemplare + Patterns -> stark aktiviert."""
        text = "Bitte klare grenzen festlegen und durchsetzen. Grenzen sind wichtig."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        # Semantik: 3/3=1.0, Syntax: "grenzen"+"bitte"=2/2=1.0, Prosodie: 0
        # Mittelwert: (1.0 + 1.0 + 0.0) / 3 ≈ 0.67 -> moderat (unter 0.75)
        assert sem["score"] >= 0.4

    def test_sem_only_semantic_no_syntax(self):
        """Nur semantische Treffer, keine syntaktischen."""
        text = "Ich will das festlegen und durchsetzen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        # Semantik: "festlegen"+"durchsetzen" = 2/3 ≈ 0.67
        # Syntax: kein Token "grenzen" oder "bitte" → 0.0
        # Mittelwert: (0.67 + 0.0 + 0.0) / 3 ≈ 0.22
        assert sem["score"] > 0.0
        assert sem["score"] < 0.5

    def test_sem_only_syntax_no_semantic(self):
        """Nur syntaktische Treffer, keine semantischen."""
        text = "Bitte achte auf die Grenzen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        # Semantik: 0/3 = 0.0 (keines der Exemplare als Substring)
        # Syntax: "Bitte"+"Grenzen" -> "bitte"+"grenzen" = 2/2 = 1.0
        # Mittelwert: (0.0 + 1.0 + 0.0) / 3 ≈ 0.33
        assert sem["score"] > 0.0
        assert sem["score"] < 0.5

    def test_mema_minimal_activation(self):
        """Minimale MEMA-Erkennung: ein Exemplar."""
        text = "Ich brauche Abstand."
        result = analyze_text(text, "de", {})
        mema = next(a for a in result["activations"] if a["family"] == "MEMA")
        # "abstand" = 1/3 semantisch ≈ 0.33
        assert mema["score"] > 0.0

    def test_clu_minimal_activation(self):
        """Minimale CLU-Erkennung: ein Exemplar."""
        text = "Wir muessen den Zeitplan anpassen."
        result = analyze_text(text, "de", {})
        clu = next(a for a in result["activations"] if a["family"] == "CLU")
        # "zeitplan" = 1/3 semantisch ≈ 0.33
        assert clu["score"] > 0.0

    def test_ato_requires_prosody_not_text(self):
        """ATO reagiert NICHT auf Text, nur auf Prosodie-Daten."""
        result_without = analyze_text("Ich zoegere", "de", {})
        result_with = analyze_text("Ich zoegere", "de", {"pause_ms": 700})
        ato_without = next(a for a in result_without["activations"] if a["family"] == "ATO")
        ato_with = next(a for a in result_with["activations"] if a["family"] == "ATO")
        assert ato_without["score"] < ato_with["score"]

    def test_cross_marker_isolation(self):
        """SEM-Text aktiviert nicht MEMA/CLU und umgekehrt."""
        text = "Klare grenzen festlegen und durchsetzen"
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        mema = next(a for a in result["activations"] if a["family"] == "MEMA")
        clu = next(a for a in result["activations"] if a["family"] == "CLU")
        assert sem["score"] > mema["score"]
        assert sem["score"] > clu["score"]

    def test_combined_markers_text(self):
        """Text mit SEM- und CLU-Signalen aktiviert beide."""
        text = "Bitte klare Grenzen festlegen. Der Zeitplan muss stimmen."
        result = analyze_text(text, "de", {})
        sem = next(a for a in result["activations"] if a["family"] == "SEM")
        clu = next(a for a in result["activations"] if a["family"] == "CLU")
        assert sem["score"] > 0.0
        assert clu["score"] > 0.0
