# Social Mirror – Getting Started

## Voraussetzungen
- Python 3.11
- Node.js 20
- npm

## Setup
1. Virtuelle Umgebung und Abhängigkeiten installieren:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r apps/backend/requirements.txt
   bash scripts/setup_spacy_de.sh
   ```
2. Frontend-Abhängigkeiten installieren:
   ```bash
   cd apps/frontend
   npm install
   cd ../../
   ```

## Entwicklung
- Backend starten:
  ```bash
  uvicorn apps.backend.app.main:app --reload --port 8000
  ```
- Frontend starten:
  ```bash
  cd apps/frontend
  npm run dev
  ```

## Testaufruf
```bash
curl -s localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text":"Ich brauche klare Grenzen.","prosody":{"pause_ms":750}}'
```
