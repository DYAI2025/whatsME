# Social Mirror – Verhaltensmarker-Analyse fuer Messenger-Konversationen

Social Mirror ist ein **deutschsprachiges Analyse-System**, das Textnachrichten (z.B. aus WhatsApp) auf psychologische und kommunikative Verhaltensmuster untersucht. Es basiert auf dem **LeanDeep-Framework (LD-3.5)** und erkennt vier Marker-Familien mittels semantischer, syntaktischer und prosodischer Detektoren.

---

## Inhaltsverzeichnis

1. [Ueberblick und Zweck](#ueberblick-und-zweck)
2. [Architektur](#architektur)
3. [Marker-System (LeanDeep LD-3.5)](#marker-system-leandeep-ld-35)
4. [Detektoren im Detail](#detektoren-im-detail)
5. [Scoring und Interpretation](#scoring-und-interpretation)
6. [API-Endpunkte](#api-endpunkte)
7. [Frontend](#frontend)
8. [Datenfluss (Ende-zu-Ende)](#datenfluss-ende-zu-ende)
9. [Verzeichnisstruktur](#verzeichnisstruktur)
10. [Installation und Start](#installation-und-start)
11. [Docker-Deployment](#docker-deployment)
12. [Konfiguration](#konfiguration)
13. [Git-Submodule](#git-submodule)
14. [Technologie-Stack](#technologie-stack)

---

## Ueberblick und Zweck

Social Mirror analysiert Texteingaben und erkennt kommunikative Verhaltensmuster, die in Verhandlungs- und Konfliktsituationen relevant sind. Das System identifiziert vier Kategorien:

| Kuerzel | Name | Erkennt |
|---------|------|---------|
| **SEM** | Grenzensetzung | Klare Positionierung und Abgrenzung |
| **MEMA** | Rueckzugssignal | Distanzierung und verminderte Offenheit |
| **CLU** | Zeit-/Budget-Thematik | Diskussionen um Verfuegbarkeit und Priorisierung |
| **ATO** | Zoegerlichkeit | Prosodische Hinweise auf Unsicherheit (Pausen) |

Jeder erkannte Marker wird mit einem Score (0-1), einer Unsicherheitsmetrik, maschinenlesbarer Evidenz und einer menschenlesbaren Interpretation in deutscher Sprache zurueckgegeben.

---

## Architektur

```
+---------------------+         POST /analyze/text         +---------------------+
|                     |  ---------------------------------> |                     |
|   React-Frontend    |                                     |   FastAPI-Backend   |
|   (Vite, Port 5173) |  <--------------------------------- |   (Uvicorn, Port    |
|                     |         JSON: Activations           |    8000)            |
+---------------------+                                     +---------------------+
                                                                      |
                                                            +---------------------+
                                                            |   Analyse-Pipeline  |
                                                            |                     |
                                                            | 1. Marker-Registry  |
                                                            | 2. Drei Detektoren  |
                                                            | 3. Score-Aggregation|
                                                            | 4. Interpretation   |
                                                            +---------------------+
                                                                      |
                                                            +---------------------+
                                                            |   Marker-Registry   |
                                                            |   (YAML, LD-3.5)   |
                                                            +---------------------+
```

Das System besteht aus drei Hauptkomponenten:

- **Backend** (FastAPI/Python): Nimmt Text entgegen, fuehrt die Marker-Erkennung durch und liefert strukturierte Ergebnisse.
- **Frontend** (React/TypeScript): Eingabefeld fuer Text, Darstellung der Ergebnisse mit Score-Balken und Evidenz-Chips.
- **Marker-Registry** (YAML): Deklarative Definition der vier LeanDeep-Marker mit Metadaten.

---

## Marker-System (LeanDeep LD-3.5)

### Was sind Marker?

Marker sind definierte Verhaltensmuster in gesprochener oder geschriebener Sprache. Jeder Marker gehoert zu einer **Familie** und wird durch ein Schema versioniert (aktuell `LD-3.5`).

### Die vier Marker-Familien

#### SEM_BOUNDARY_SETTING (Familie: SEM)

**Zweck:** Erkennt Aussagen, die klare Grenzen setzen oder Positionen beziehen.

- **Semantische Schluesselwoerter:** "klare grenzen", "festlegen", "durchsetzen"
- **Syntaktische Muster:** "grenzen", "bitte"
- **Beispielsatz:** *"Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um."*

#### MEMA_WITHDRAWAL_SIGNAL (Familie: MEMA)

**Zweck:** Erkennt Rueckzugsverhalten und sprachliche Distanzierung.

- **Semantische Schluesselwoerter:** "ich ziehe mich", "abstand", "zurueckziehen"
- **Syntaktische Muster:** "ruhe", "allein"
- **Beispielsatz:** *"Ich ziehe mich erstmal zurueck, brauche Abstand."*

#### CLU_TOPIC_BUDGET_TIME (Familie: CLU)

**Zweck:** Erkennt thematische Auseinandersetzung mit Zeit, Verfuegbarkeit und Priorisierung.

- **Semantische Schluesselwoerter:** "zeitplan", "budget", "zeitrahmen"
- **Syntaktische Muster:** "zeit", "plan"
- **Beispielsatz:** *"Wir muessen den Zeitplan anpassen, das Budget reicht nicht."*

#### ATO_HESITATION_VOICE (Familie: ATO)

**Zweck:** Erkennt Zoegerlichkeit anhand prosodischer Merkmale (Sprechpausen).

- **Detektor:** Ausschliesslich Prosodie (keine Textanalyse)
- **Schwellenwert:** Pausen ueber 700ms erzeugen Signal
- **Anwendungsfall:** Audiotranskriptionen mit Pauseninformation

### Marker-Definition (YAML)

Jeder Marker ist in `marker_registry/LD-3.5/<FAMILIE>/<CODE>.yaml` definiert:

```yaml
code: SEM_BOUNDARY_SETTING
family: SEM
schema: LD-3.5
description: "Signals boundary setting statements in negotiations."
```

Im Code werden die Marker zusaetzlich als `MarkerRegistry` geladen (`app/core/registry.py`), die als In-Memory-Lookup fuer die Analyse-Pipeline dient.

---

## Detektoren im Detail

Die Analyse-Pipeline verwendet drei unabhaengige Detektoren, die jeweils einen Score zwischen 0.0 und 1.0 liefern.

### 1. Semantischer Detektor (`detectors/embedding.py`)

**Mechanik:** Substring-Matching gegen vordefinierte Exemplare (Schluesselphrasen).

```
Score = Anzahl gefundener Exemplare / Gesamtanzahl Exemplare
```

- Der eingegebene Text wird in Kleinbuchstaben umgewandelt.
- Fuer jeden Marker existiert eine Liste von Exemplar-Phrasen (z.B. "klare grenzen", "festlegen", "durchsetzen" fuer SEM).
- Jede Phrase, die als Substring im Text vorkommt, zaehlt als Treffer.
- Der Score ist der Anteil der getroffenen Phrasen (0.0 bis 1.0).

**Beispiel:** Text *"Ich muss klare Grenzen festlegen"* gegen SEM-Exemplare ("klare grenzen", "festlegen", "durchsetzen") ergibt Score = 2/3 = 0.67.

### 2. Syntaktischer Detektor (`detectors/dep.py`)

**Mechanik:** Token-Matching gegen Schluesselwoerter (vereinfachte Dependency-Analyse).

```
Score = Anzahl gefundener Muster-Tokens / Gesamtanzahl Muster-Tokens
```

- Der Text wird an Leerzeichen in Tokens aufgeteilt.
- Alle Tokens werden in Kleinbuchstaben normalisiert.
- Fuer jeden Marker existiert eine Liste von Muster-Tokens (z.B. "grenzen", "bitte" fuer SEM).
- Gefundene Tokens ergeben den Treffer-Anteil.

**Beispiel:** Text *"Bitte setzen wir Grenzen"* gegen SEM-Muster ("grenzen", "bitte") ergibt Score = 2/2 = 1.0.

### 3. Prosodie-Detektor (`detectors/prosody.py`)

**Mechanik:** Heuristik basierend auf Pausendauer (in Millisekunden).

```
Score = min(1.0, pause_ms / 700.0)
```

- Nur aktiv fuer die ATO-Familie (Zoegerlichkeit).
- Pauses <= 0ms ergeben Score 0.0.
- 700ms Pause ergibt Score 1.0 (Maximum).
- Werte dazwischen werden linear interpoliert.
- Erwartet `prosody.pause_ms` als Eingabe im Request.

**Beispiel:** `pause_ms: 750` ergibt `min(1.0, 750/700) = 1.0`.

---

## Scoring und Interpretation

### Score-Aggregation (`core/scoring.py`)

Die drei Detektor-Scores werden durch einfache Mittelwertbildung aggregiert:

```
Gesamtscore = Mittelwert aller Detektor-Scores (ohne None-Werte)
```

Fuer textbasierte Marker (SEM, MEMA, CLU) fliessen Semantik und Syntax ein; Prosodie ist 0.0. Fuer ATO fliesst ausschliesslich der Prosodie-Score ein (Semantik und Syntax sind 0.0).

### Unsicherheitsberechnung

```
Unsicherheit = max(0.0, 1 - Gesamtscore)
```

Je hoeher der Score, desto geringer die Unsicherheit. Ein Score von 0.8 ergibt eine Unsicherheit von 0.2 (20%).

### Menschenlesbare Interpretation (`core/interpret.py`)

Basierend auf dem Gesamtscore wird ein deutscher Interpretationstext generiert:

| Score-Bereich | Interpretation |
|---------------|----------------|
| >= 0.75 | `"{MARKER} ist stark aktiviert."` |
| >= 0.40 | `"{MARKER} zeigt moderate Aktivitaet."` |
| > 0.00 | `"{MARKER} hat nur leichte Hinweise."` |
| = 0.00 | `"{MARKER} ist derzeit nicht aktiv."` |

---

## API-Endpunkte

### `GET /health`

Health-Check fuer Monitoring.

**Response:**
```json
{"status": "ok"}
```

### `POST /analyze/text`

Hauptendpunkt: Analysiert Text und liefert Marker-Aktivierungen.

**Request:**
```json
{
  "text": "Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um.",
  "lang": "de",
  "prosody": {"pause_ms": 750}
}
```

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `text` | string | ja | Zu analysierender Text |
| `lang` | string | nein | Sprachcode (Standard: `"de"`) |
| `prosody` | object | nein | Prosodische Messwerte, z.B. `{"pause_ms": 750}` |

**Response:**
```json
{
  "lang": "de",
  "activations": [
    {
      "marker": "SEM_BOUNDARY_SETTING",
      "family": "SEM",
      "score": 0.67,
      "uncertainty": 0.33,
      "interpretation": "SEM_BOUNDARY_SETTING zeigt moderate Aktivitaet.",
      "schema": "LD-3.5",
      "evidence": [
        {
          "type": "semantic",
          "detail": "Semantische Beispiele lieferten einen Score von 0.67.",
          "span": null
        },
        {
          "type": "syntax",
          "detail": "Abhaengigkeitsmuster unterstuetzten den Marker mit 0.50.",
          "span": null
        }
      ]
    }
  ]
}
```

Jedes `ActivationEvent` enthaelt:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `marker` | string | Marker-Code (z.B. `SEM_BOUNDARY_SETTING`) |
| `family` | string | Familie (`SEM`, `MEMA`, `CLU`, `ATO`) |
| `score` | float | Aggregierter Score (0.0–1.0) |
| `uncertainty` | float | Unsicherheit (0.0–1.0) |
| `interpretation` | string | Menschenlesbare Deutung (Deutsch) |
| `schema` | string | LeanDeep-Schema-Version (`LD-3.5`) |
| `evidence` | array | Liste der Einzel-Evidenzen pro Detektor |

### `POST /ingest/events`

Platzhalter fuer die kuenftige WhatsApp-Nachrichtenaufnahme.

**Request:**
```json
{
  "source": "WhatsApp",
  "payload": {"message": "...", "contact_id": "wa:+4917..."}
}
```

**Response:**
```json
{"status": "accepted", "source": "WhatsApp"}
```

---

## Frontend

### Marker Probe Panel

Das Frontend ist eine Single-Page-Applikation (SPA) ohne Routing, die als interaktives Analyse-Werkzeug dient.

### Bestandteile

**App.tsx** – Hauptkomponente:
- Textarea fuer Texteingabe (vorbelegt mit Beispieltext)
- "Analysieren"-Button sendet POST an `/analyze/text`
- Zeigt je Aktivierung eine Ergebniskarte an
- Sendet standardmaessig `prosody: {pause_ms: 750}` mit

**ScoreBar.tsx** – Score-Visualisierung:
- Horizontaler Fortschrittsbalken (0–100%)
- Gruen (`#16a34a`) bei Score > 0.6
- Gelb (`#fbbf24`) bei Score <= 0.6

**EvidenceChips.tsx** – Evidenz-Anzeige:
- Zeigt jeden Detektor-Befund als Chip/Badge an
- Darstellung: Typ (fett) + Detail-Text

### Ablauf im Frontend

1. Nutzer gibt deutschen Text in das Textfeld ein
2. Klick auf "Analysieren" sendet den Text ans Backend
3. Waehrend der Analyse wird "Analysiere..." angezeigt
4. Ergebnis: Eine Karte pro erkanntem Marker mit:
   - Marker-Name und Familie
   - Visueller Score-Balken mit Prozentwert
   - Menschenlesbare Interpretation
   - Evidenz-Chips mit Detail-Informationen
   - Unsicherheitswert

---

## Datenfluss (Ende-zu-Ende)

```
1. Nutzer-Eingabe (Text + optionale Prosodie)
         |
         v
2. POST /analyze/text  (Frontend -> Backend)
         |
         v
3. analyzer.py: Iteration ueber alle 4 Marker
         |
         +---> Fuer jeden Marker:
         |       |
         |       +---> Semantischer Detektor: Exemplar-Substring-Matching
         |       |     -> Score 0.0-1.0
         |       |
         |       +---> Syntaktischer Detektor: Token-Pattern-Matching
         |       |     -> Score 0.0-1.0
         |       |
         |       +---> Prosodie-Detektor: Pausendauer-Heuristik (nur ATO)
         |       |     -> Score 0.0-1.0
         |       |
         |       +---> Score-Aggregation: Mittelwert der Detektoren
         |       |
         |       +---> Evidenz-Aufbau: Liste der Einzel-Befunde
         |       |
         |       +---> Interpretation: Deutscher Text nach Score-Schwelle
         |
         v
4. JSON-Response mit allen ActivationEvents
         |
         v
5. Frontend rendert Ergebnis-Karten
         |
         +---> ScoreBar (visueller Balken)
         +---> EvidenceChips (Detektor-Befunde)
         +---> Interpretation (lesbare Deutung)
         +---> Unsicherheitswert
```

---

## Verzeichnisstruktur

```
social-mirror/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py                 # FastAPI-Einstiegspunkt, CORS, Router
│   │   │   ├── routes/
│   │   │   │   ├── analyze.py          # POST /analyze/text Endpunkt
│   │   │   │   └── ingest.py           # POST /ingest/events Platzhalter
│   │   │   ├── core/
│   │   │   │   ├── registry.py         # Marker-Registry (In-Memory)
│   │   │   │   ├── detectors/
│   │   │   │   │   ├── embedding.py    # Semantischer Detektor
│   │   │   │   │   ├── dep.py          # Syntaktischer Detektor
│   │   │   │   │   └── prosody.py      # Prosodie-Detektor
│   │   │   │   ├── scoring.py          # Score-Aggregation
│   │   │   │   └── interpret.py        # Menschenlesbare Interpretation
│   │   │   ├── models/
│   │   │   │   ├── schemas.py          # Pydantic-Datenmodelle
│   │   │   │   └── db.py              # Platzhalter fuer Persistenz
│   │   │   └── services/
│   │   │       └── analyzer.py         # Analyse-Orchestrierung
│   │   ├── requirements.txt            # Python-Abhaengigkeiten
│   │   └── .env.example                # Umgebungsvariablen-Vorlage
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── main.tsx                # React-Einstiegspunkt
│   │   │   ├── App.tsx                 # Hauptkomponente
│   │   │   └── components/
│   │   │       ├── ScoreBar.tsx        # Score-Balken
│   │   │       └── EvidenceChips.tsx   # Evidenz-Chips
│   │   ├── index.html                  # HTML-Einstiegspunkt + CSS
│   │   ├── package.json                # Node-Abhaengigkeiten
│   │   ├── vite.config.ts              # Vite-Konfiguration
│   │   └── tsconfig.json               # TypeScript-Konfiguration
│   └── ingestion/                      # WhatsApp-Collector (Submodul)
├── marker_registry/
│   └── LD-3.5/                         # LeanDeep 3.5 Marker-Definitionen
│       ├── SEM/SEM_BOUNDARY_SETTING.yaml
│       ├── MEMA/MEMA_WITHDRAWAL_SIGNAL.yaml
│       ├── CLU/CLU_TOPIC_BUDGET_TIME.yaml
│       └── ATO/ATO_HESITATION_VOICE.yaml
├── scripts/
│   ├── setup_spacy_de.sh               # spaCy-Deutsch-Modell Setup
│   └── seed_examples.sh                # Test-Daten-Seeding
├── docker/
│   ├── Dockerfile.backend              # Backend-Container
│   └── Dockerfile.frontend             # Frontend-Container
├── docs/
│   └── GETTING_STARTED.md              # Kurzanleitung
├── docker-compose.yml                  # Multi-Container-Orchestrierung
├── Makefile                            # Build-Automatisierung
└── .gitmodules                         # Submodul-Konfiguration
```

---

## Installation und Start

### Voraussetzungen

- Python 3.11+
- Node.js 20+
- Git (fuer Submodule)

### Lokale Entwicklung

```bash
# 1. Repository klonen (mit Submodulen)
git clone --recurse-submodules <REPO_URL>
cd social-mirror

# 2. Python-Umgebung + Abhaengigkeiten
python -m venv .venv
source .venv/bin/activate
pip install -r apps/backend/requirements.txt
bash scripts/setup_spacy_de.sh

# 3. Frontend-Abhaengigkeiten
cd apps/frontend && npm install && cd ../..

# 4. Backend starten (Terminal 1)
uvicorn apps.backend.app.main:app --reload --port 8000

# 5. Frontend starten (Terminal 2)
cd apps/frontend && npm run dev
```

Oder per Makefile:

```bash
make setup       # Alles installieren
make run         # Backend starten
make dev-frontend  # Frontend starten (separates Terminal)
```

### Test-Aufruf

```bash
curl -s localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um.",
    "lang": "de",
    "prosody": {"pause_ms": 750}
  }' | python -m json.tool
```

---

## Docker-Deployment

```bash
# Beide Services starten
docker-compose up --build

# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
```

### Container-Details

| Service | Basis-Image | Port | Beschreibung |
|---------|-------------|------|--------------|
| `backend` | `python:3.11-slim` | 8000 | FastAPI + spaCy-Deutsch-Modell |
| `frontend` | `node:20-alpine` | 5173 | Vite Dev-Server mit React |

Das Frontend haengt via `depends_on` vom Backend ab, startet also erst nach diesem.

---

## Konfiguration

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|----------|----------|--------------|
| `ALLOWED_ORIGINS` | `*` | CORS-erlaubte Origins (kommasepariert) |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding-Modell (fuer kuenftige ML-Integration) |
| `OPENAI_API_KEY` | - | Optional fuer kuenftige ML-Features |
| `SENTRY_DSN` | - | Optional fuer Error-Tracking |

### Fest konfigurierte Werte

| Parameter | Wert | Ort |
|-----------|------|-----|
| Sprache | Deutsch (`de`) | Exemplare, Interpretation |
| Prosodie-Schwelle | 700ms | `detectors/prosody.py` |
| Score-Interpretationsschwellen | 0.75 / 0.40 / 0.0 | `core/interpret.py` |
| Marker-Schema | LD-3.5 | `marker_registry/` + `registry.py` |

---

## Git-Submodule

Das Repository referenziert drei externe Submodule:

| Submodul | Pfad | Zweck |
|----------|------|-------|
| [whatsthat](https://github.com/markrai/whatsthat.git) | `apps/ingestion/whatsthat` | WhatsApp-Nachrichtencollector |
| [WTME_ALL_Marker](https://github.com/DYAI2025/WTME_ALL_Marker-LD3.4.1-5.1.git) | `vendor/WTME` | Erweitertes Marker-Verzeichnis (LD 3.4.1–5.1) |
| [LeanDeep_Framework](https://github.com/DYAI2025/LeanDeep_Framework_v4.0.git) | `vendor/LeanDeep` | LeanDeep-Framework v4.0 |

```bash
# Submodule initialisieren
git submodule update --init --recursive
```

---

## Technologie-Stack

### Backend

| Technologie | Version | Zweck |
|-------------|---------|-------|
| Python | 3.11+ | Laufzeitumgebung |
| FastAPI | >= 0.111 | Web-Framework |
| Uvicorn | >= 0.30 | ASGI-Server |
| Pydantic | >= 2.8 | Datenvalidierung |
| PyYAML | >= 6.0 | YAML-Parsing |
| spaCy | >= 3.7 | NLP (Deutsch-Modell `de_core_news_md`) |
| sentence-transformers | >= 2.7 | Semantische Embeddings (kuenftig) |
| NumPy | >= 1.26 | Numerische Berechnungen |

### Frontend

| Technologie | Version | Zweck |
|-------------|---------|-------|
| React | 18.x | UI-Framework |
| TypeScript | 5.4+ | Typsicherheit |
| Vite | 5.3+ | Build-Tool und Dev-Server |

### Infrastruktur

| Technologie | Zweck |
|-------------|-------|
| Docker | Containerisierung |
| Docker Compose | Multi-Service-Orchestrierung |
| Make | Build-Automatisierung |
