"""QA-Tests fuer die API-Endpunkte (routes + main.py).

Prueft: HTTP-Endpunkte, Request-Validierung, Response-Struktur, CORS.
"""

import pytest


# ---------------------------------------------------------------------------
# Health-Endpunkt
# ---------------------------------------------------------------------------

class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        """GET /health -> 200 OK."""
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_ok_status(self, client):
        """GET /health -> {"status": "ok"}."""
        resp = client.get("/health")
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Analyze-Endpunkt: Positiv-Tests
# ---------------------------------------------------------------------------

class TestAnalyzeEndpointPositive:
    """Korrekte Analyse-Requests."""

    def test_analyze_returns_200(self, client):
        """POST /analyze/text mit gueltigem Body -> 200."""
        resp = client.post("/analyze/text", json={
            "text": "Ich brauche klare Grenzen.",
            "lang": "de",
        })
        assert resp.status_code == 200

    def test_analyze_response_structure(self, client):
        """Response enthaelt 'lang' und 'activations'."""
        resp = client.post("/analyze/text", json={"text": "Test"})
        data = resp.json()
        assert "lang" in data
        assert "activations" in data
        assert isinstance(data["activations"], list)

    def test_analyze_returns_four_activations(self, client):
        """Immer vier Aktivierungen in der Response."""
        resp = client.post("/analyze/text", json={"text": "Test"})
        assert len(resp.json()["activations"]) == 4

    def test_analyze_with_prosody(self, client):
        """Request mit Prosodie-Daten wird akzeptiert."""
        resp = client.post("/analyze/text", json={
            "text": "Aehm...",
            "lang": "de",
            "prosody": {"pause_ms": 750},
        })
        assert resp.status_code == 200
        ato = next(a for a in resp.json()["activations"] if a["family"] == "ATO")
        assert ato["score"] > 0.0

    def test_analyze_default_lang_is_de(self, client):
        """Ohne 'lang' wird 'de' als Standard verwendet."""
        resp = client.post("/analyze/text", json={"text": "Hallo"})
        assert resp.json()["lang"] == "de"

    def test_analyze_with_null_prosody(self, client):
        """prosody: null wird als leeres Dict behandelt."""
        resp = client.post("/analyze/text", json={
            "text": "Hallo",
            "prosody": None,
        })
        assert resp.status_code == 200

    def test_analyze_sem_detection_via_api(self, client):
        """SEM-Erkennung funktioniert ueber den API-Endpunkt."""
        resp = client.post("/analyze/text", json={
            "text": "Wir muessen klare grenzen festlegen und durchsetzen. Bitte Grenzen setzen.",
        })
        sem = next(a for a in resp.json()["activations"] if a["family"] == "SEM")
        assert sem["score"] > 0.3

    def test_activation_fields_complete(self, client):
        """Jede Aktivierung hat alle Pflichtfelder ueber API."""
        resp = client.post("/analyze/text", json={"text": "Test"})
        required = {"marker", "family", "score", "uncertainty",
                    "interpretation", "schema", "evidence"}
        for a in resp.json()["activations"]:
            assert required.issubset(a.keys())


# ---------------------------------------------------------------------------
# Analyze-Endpunkt: Negativ-Tests
# ---------------------------------------------------------------------------

class TestAnalyzeEndpointNegative:
    """Fehlerhafte Requests -> korrekte Fehlerbehandlung."""

    def test_missing_text_field_returns_422(self, client):
        """Pflichtfeld 'text' fehlt -> 422 Validation Error."""
        resp = client.post("/analyze/text", json={"lang": "de"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        """Leerer Body -> 422."""
        resp = client.post("/analyze/text", json={})
        assert resp.status_code == 422

    def test_no_json_body_returns_422(self, client):
        """Kein JSON-Body -> 422."""
        resp = client.post("/analyze/text", content=b"not json",
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 422

    def test_wrong_http_method_returns_405(self, client):
        """GET auf /analyze/text -> 405 Method Not Allowed."""
        resp = client.get("/analyze/text")
        assert resp.status_code == 405

    def test_nonexistent_route_returns_404(self, client):
        """Unbekannter Pfad -> 404."""
        resp = client.get("/does-not-exist")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Ingest-Endpunkt: Positiv-Tests
# ---------------------------------------------------------------------------

class TestIngestEndpointPositive:
    """Korrekte Ingest-Requests."""

    def test_ingest_returns_200(self, client):
        """POST /ingest/events mit gueltigem Body -> 200."""
        resp = client.post("/ingest/events", json={
            "source": "WhatsApp",
            "payload": {"message": "Hallo"},
        })
        assert resp.status_code == 200

    def test_ingest_returns_accepted(self, client):
        """Response enthaelt status=accepted und source."""
        resp = client.post("/ingest/events", json={
            "source": "WhatsApp",
            "payload": {"msg": "Test"},
        })
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["source"] == "WhatsApp"

    def test_ingest_accepts_any_source(self, client):
        """Beliebiger Source-String wird akzeptiert."""
        resp = client.post("/ingest/events", json={
            "source": "Telegram",
            "payload": {},
        })
        assert resp.json()["source"] == "Telegram"


# ---------------------------------------------------------------------------
# Ingest-Endpunkt: Negativ-Tests
# ---------------------------------------------------------------------------

class TestIngestEndpointNegative:
    """Fehlerhafte Ingest-Requests."""

    def test_missing_source_returns_422(self, client):
        """Pflichtfeld 'source' fehlt -> 422."""
        resp = client.post("/ingest/events", json={"payload": {}})
        assert resp.status_code == 422

    def test_missing_payload_returns_422(self, client):
        """Pflichtfeld 'payload' fehlt -> 422."""
        resp = client.post("/ingest/events", json={"source": "WhatsApp"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        """Leerer Body -> 422."""
        resp = client.post("/ingest/events", json={})
        assert resp.status_code == 422
