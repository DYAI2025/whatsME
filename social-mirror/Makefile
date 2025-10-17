.PHONY: setup run dev-frontend

setup:
python -m venv .venv && . .venv/bin/activate && pip install -r apps/backend/requirements.txt && bash scripts/setup_spacy_de.sh && cd apps/frontend && npm i

run:
uvicorn apps.backend.app.main:app --reload --port 8000

dev-frontend:
cd apps/frontend && npm run dev
