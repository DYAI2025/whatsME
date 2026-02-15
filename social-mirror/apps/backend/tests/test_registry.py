"""QA-Tests fuer die Marker-Registry (registry.py).

Prueft: In-Memory-Registry, Marker-Lookup, Vollstaendigkeit der vier LeanDeep-Marker.
"""

import pytest

from app.core.registry import DEFAULT_MARKERS, Marker, MarkerRegistry


# ---------------------------------------------------------------------------
# Positiv-Tests (Happy Path)
# ---------------------------------------------------------------------------

class TestRegistryPositive:
    """Korrekte Funktion der Marker-Registry."""

    def test_default_registry_has_four_markers(self):
        """Genau vier Marker in DEFAULT_MARKERS."""
        markers = DEFAULT_MARKERS.all()
        assert len(markers) == 4

    def test_sem_marker_exists(self):
        """SEM_BOUNDARY_SETTING ist registriert."""
        marker = DEFAULT_MARKERS.get("SEM_BOUNDARY_SETTING")
        assert marker is not None
        assert marker.family == "SEM"
        assert marker.schema == "LD-3.5"

    def test_mema_marker_exists(self):
        """MEMA_WITHDRAWAL_SIGNAL ist registriert."""
        marker = DEFAULT_MARKERS.get("MEMA_WITHDRAWAL_SIGNAL")
        assert marker is not None
        assert marker.family == "MEMA"
        assert marker.schema == "LD-3.5"

    def test_clu_marker_exists(self):
        """CLU_TOPIC_BUDGET_TIME ist registriert."""
        marker = DEFAULT_MARKERS.get("CLU_TOPIC_BUDGET_TIME")
        assert marker is not None
        assert marker.family == "CLU"
        assert marker.schema == "LD-3.5"

    def test_ato_marker_exists(self):
        """ATO_HESITATION_VOICE ist registriert."""
        marker = DEFAULT_MARKERS.get("ATO_HESITATION_VOICE")
        assert marker is not None
        assert marker.family == "ATO"
        assert marker.schema == "LD-3.5"

    def test_all_markers_have_ld35_schema(self):
        """Alle Marker verwenden Schema LD-3.5."""
        for marker in DEFAULT_MARKERS.all():
            assert marker.schema == "LD-3.5", f"{marker.code} hat Schema {marker.schema}"

    def test_all_markers_have_description(self):
        """Alle Marker haben eine nicht-leere Beschreibung."""
        for marker in DEFAULT_MARKERS.all():
            assert marker.description, f"{marker.code} hat keine Beschreibung"

    def test_marker_is_frozen_dataclass(self):
        """Marker-Instanzen sind immutable (frozen)."""
        marker = DEFAULT_MARKERS.get("SEM_BOUNDARY_SETTING")
        with pytest.raises(AttributeError):
            marker.code = "MANIPULATED"

    def test_custom_registry_creation(self):
        """Eigene Registry kann mit beliebigen Markern erstellt werden."""
        custom = MarkerRegistry([
            Marker(family="TEST", code="TEST_MARKER", schema="LD-TEST", description="Test"),
        ])
        assert len(custom.all()) == 1
        assert custom.get("TEST_MARKER") is not None

    def test_all_families_unique(self):
        """Jede Familie ist genau einmal vertreten (SEM, MEMA, CLU, ATO)."""
        families = {m.family for m in DEFAULT_MARKERS.all()}
        assert families == {"SEM", "MEMA", "CLU", "ATO"}


# ---------------------------------------------------------------------------
# Negativ-Tests (Falsche Eingabe -> erwartetes Verhalten)
# ---------------------------------------------------------------------------

class TestRegistryNegative:
    """Korrektes Verhalten bei nicht existierendem Lookup."""

    def test_unknown_code_returns_none(self):
        """Unbekannter Marker-Code -> None."""
        result = DEFAULT_MARKERS.get("DOES_NOT_EXIST")
        assert result is None

    def test_empty_string_returns_none(self):
        """Leerer String -> None."""
        result = DEFAULT_MARKERS.get("")
        assert result is None

    def test_empty_registry(self):
        """Leere Registry hat keine Marker."""
        empty = MarkerRegistry([])
        assert len(empty.all()) == 0
        assert empty.get("SEM_BOUNDARY_SETTING") is None

    def test_case_sensitive_lookup(self):
        """Lookup ist case-sensitive: 'sem_boundary_setting' != 'SEM_BOUNDARY_SETTING'."""
        assert DEFAULT_MARKERS.get("sem_boundary_setting") is None
