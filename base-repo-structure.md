Hier ist ein voller Repo‑Skeleton mit lauffähigem Backend (FastAPI), vier LD‑Marker (SEM/MEMA/CLU/ATO), heuristischer Aktivierung ohne Regex, Endpoint /analyze/text → ActivationEvent inkl. Evidenz‑Chips, plus ein schlankes React‑Frontend mit Scorebar und menschenlesbarer Interpretation.

1. Verzeichnisbaum
   social-mirror/
   ├─ apps/
   │ ├─ backend/
   │ │ ├─ app/
   │ │ │ ├─ main.py
   │ │ │ ├─ routes/
   │ │ │ │ ├─ analyze.py
   │ │ │ │ └─ ingest.py
   │ │ │ ├─ core/
   │ │ │ │ ├─ registry.py
   │ │ │ │ ├─ detectors/
   │ │ │ │ │ ├─ embedding.py
   │ │ │ │ │ ├─ dep.py
   │ │ │ │ │ └─ prosody.py
   │ │ │ │ ├─ scoring.py
   │ │ │ │ └─ interpret.py
   │ │ │ ├─ models/
   │ │ │ │ ├─ schemas.py
   │ │ │ │ └─ db.py
   │ │ │ └─ services/
   │ │ │ └─ analyzer.py
   │ │ ├─ requirements.txt
   │ │ └─ .env.example
   │ ├─ frontend/
   │ │ ├─ index.html
   │ │ ├─ package.json
   │ │ ├─ vite.config.ts
   │ │ └─ src/
   │ │ ├─ main.tsx
   │ │ ├─ App.tsx
   │ │ └─ components/
   │ │ ├─ ScoreBar.tsx
   │ │ └─ EvidenceChips.tsx
   │ └─ ingestion/
   │ └─ whatsthat/ # Submodule (Collector)
   ├─ marker_registry/
   │ └─ LD-3.5/
   │ ├─ SEM/SEM_BOUNDARY_SETTING.yaml
   │ ├─ MEMA/MEMA_WITHDRAWAL_SIGNAL.yaml
   │ ├─ CLU/CLU_TOPIC_BUDGET_TIME.yaml
   │ └─ ATO/ATO_HESITATION_VOICE.yaml
   ├─ scripts/
   │ ├─ setup_spacy_de.sh
   │ └─ seed_examples.sh
   ├─ docker/
   │ ├─ Dockerfile.backend
   │ └─ Dockerfile.frontend
   ├─ docker-compose.yml
   ├─ docs/GETTING_STARTED.md
   └─ Makefile

2. Submodule & Setup

# Neues Repo

mkdir social-mirror && cd social-mirror && git init

# Submodule einbinden

git submodule add https://github.com/markrai/whatsthat.git apps/ingestion/whatsthat

# Optionale Marker-Bestände als Vendor (später für Ausbau)

git submodule add https://github.com/DYAI2025/WTME_ALL_Marker-LD3.4.1-5.1.git vendor/WTME
git submodule add https://github.com/DYAI2025/LeanDeep_Framework_v4.0.git vendor/LeanDeep

# Python/Node vorbereiten

python -m venv .venv && source .venv/bin/activate
pip install -r apps/backend/requirements.txt
bash scripts/setup_spacy_de.sh

cd apps/frontend && npm i && cd ../../

# Start (2 Terminals) – Backend & Frontend

uvicorn apps.backend.app.main:app --reload --port 8000
cd apps/frontend && npm run dev

3. Backend – Kerncode

apps/backend/requirements.txt

fastapi>=0.111
uvicorn[standard]>=0.30
pydantic>=2.8
pyyaml>=6.0
numpy>=1.26
sentence-transformers>=2.7
spacy>=3.7

apps/backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import analyze, ingest

app = FastAPI(title="SocialMirror HMA", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])

@app.get("/health")
def health():
return {"status": "ok"}

apps/backend/app/routes/analyze.py

from fastapi import APIRouter
from pydantic import BaseModel
from ..services.analyzer import analyze_text

router = APIRouter()

class AnalyzeReq(BaseModel):
text: str
lang: str = "de"
prosody: dict | None = None
meta: dict | None = None

@router.post("/text")
def analyze_text_route(req: AnalyzeReq):
return analyze_text(text=req.text, lang=req.lang, prosody=req.prosody or {}, meta=req.meta or {})

apps/backend/app/routes/ingest.py (für später – hier minimal)

from fastapi import APIRouter
router = APIRouter()

@router.post("/message")
def ingest_message(msg: dict): # hier könnte persistiert und danach analyze_text() aufgerufen werden
return {"ack": True}

apps/backend/app/models/schemas.py

from pydantic import BaseModel
from typing import List, Dict, Any

class Evidence(BaseModel):
type: str # "embedding_match" | "dep_pattern" | "prosody_feature"
detail: str # menschenlesbare Kurzbeschreibung
score: float | None = None
span: str | None = None

class Activation(BaseModel):
marker: str # e.g. "SEM.BOUNDARY_SETTING"
family: str # "SEM" | "MEMA" | "CLU" | "ATO"
score: float
uncertainty: float
evidence: List[Evidence]
interpretation: str # menschenlesbar
schema: str # "LD-3.5"

class ActivationEvent(BaseModel):
message_id: str
contact_id: str | None = None
activations: List[Activation]

apps/backend/app/core/registry.py

import os, glob, yaml

class MarkerDef:
def **init**(self, cfg: dict):
self.id = cfg["id"]
self.family = cfg["family"]
self.schema = cfg.get("ld_schema","LD-3.5")
self.signals = cfg.get("signals",[])
self.weights = cfg.get("weights",{"embedding":0.6,"dep":0.4})
self.threshold = float(cfg.get("threshold",0.6))
self.min_support = int(cfg.get("evidence",{}).get("min_support",2))

def load_ld_markers(root="marker_registry/LD-3.5"):
paths = glob.glob(os.path.join(root, "\*_/_.yaml"), recursive=True)
markers = []
for p in paths:
with open(p, "r", encoding="utf-8") as f:
cfg = yaml.safe_load(f)
markers.append(MarkerDef(cfg))
return markers

MARKERS = load_ld_markers()

apps/backend/app/core/detectors/embedding.py

from sentence_transformers import SentenceTransformer
import numpy as np

\_model = None
def get_model(name: str = "sentence-transformers/all-MiniLM-L6-v2"):
global \_model
if \_model is None:
\_model = SentenceTransformer(name)
return \_model

def cosine(a, b):
return float(np.dot(a, b) / (np.linalg.norm(a) \* np.linalg.norm(b) + 1e-9))

def run(text: str, signal: dict):
"""
signal:
type: embedding_pattern
encoder: all-MiniLM-L6-v2
positives: [..]
negatives: [..]
threshold: 0.74
"""
model = get_model(signal.get("encoder","sentence-transformers/all-MiniLM-L6-v2"))
enc = model.encode
emb_text = enc([text])[0]
pos = signal.get("positives",[])
neg = signal.get("negatives",[])
sims = []
best_phrase = None
best_sim = -1.0
for phrase in pos:
s = cosine(emb_text, enc([phrase])[0])
sims.append(s)
if s > best_sim:
best_sim, best_phrase = s, phrase # margin gegen negatives
neg_max = max([cosine(emb_text, enc([n])[0]) for n in neg], default=0.0) # effektive score
eff = max(0.0, best_sim - neg_max)
passed = eff >= float(signal.get("threshold", 0.7))
evidence = {
"type": "embedding_match",
"detail": f"Ähnlichkeit {eff:.2f} (best '{best_phrase}', neg {neg_max:.2f})",
"score": eff,
"span": best_phrase
}
return passed, eff, evidence

apps/backend/app/core/detectors/dep.py

import spacy
\_nlp = None
def \_get_nlp():
global \_nlp
if \_nlp is None:
\_nlp = spacy.load("de_core_news_md")
return \_nlp

def run(text: str, signal: dict):
"""
signal:
type: dep_pattern
pattern: { head_lemma: "setzen", dep: "obj", token_lemma: "grenze" }
"""
nlp = \_get_nlp()
doc = nlp(text)
pat = signal.get("pattern",{})
head_lemma = pat.get("head_lemma","").lower()
dep_rel = pat.get("dep","")
token_lemma = pat.get("token_lemma","").lower()

    for tok in doc:
        if tok.lemma_.lower() == token_lemma and tok.dep_ == dep_rel and tok.head.lemma_.lower() == head_lemma:
            ev = {"type":"dep_pattern","detail":f"{tok.head.lemma_}→({tok.dep_})→{tok.lemma_}","score":1.0,"span":tok.text}
            return True, 1.0, ev
    return False, 0.0, {"type":"dep_pattern","detail":"kein passender Dependenz-Treffer","score":0.0}

apps/backend/app/core/detectors/prosody.py

def run(\_text: str, signal: dict, prosody: dict):
"""
signal:
type: prosody_feature
feature: "pause_ms"
op: ">"
threshold: 600
prosody example: {"pause_ms": 800, "pitch_slope": -0.1}
"""
feature = signal.get("feature")
op = signal.get("op")
thr = float(signal.get("threshold",0))
val = float(prosody.get(feature, float("nan")))
passed = False
if feature in prosody:
if op == ">" and val > thr: passed = True
if op == "<" and val < thr: passed = True
ev = {"type":"prosody_feature","detail":f"{feature}={val} {op} {thr} → {passed}","score": (1.0 if passed else 0.0)}
return passed, (1.0 if passed else 0.0), ev

apps/backend/app/core/scoring.py

import math

def aggregate(evidences, weights): # evidences: dict with keys embedding, dep, prosody (optional)
raw = 0.0
if "embedding" in evidences and evidences["embedding"] is not None:
raw += weights.get("embedding",0.6) _ evidences["embedding"]
if "dep" in evidences and evidences["dep"] is not None:
raw += weights.get("dep",0.4) _ evidences["dep"]
if "prosody" in evidences and evidences["prosody"] is not None:
raw += weights.get("prosody",0.2) _ evidences["prosody"]
score = 1/(1+math.exp(-6_(raw-0.5))) # Sigmoid, zentriert auf 0.5
return float(score)

def uncertainty(evid_scores): # einfache Streuungsmetrik: je homogener, desto niedriger
if not evid_scores: return 1.0
m = sum(evid_scores)/len(evid_scores)
var = sum((e-m)\*\*2 for e in evid_scores)/len(evid_scores)
return float(min(1.0, max(0.0, var)))

apps/backend/app/core/interpret.py

def interpret(marker_id: str, score: float) -> str:
m = marker_id.upper()
if m == "SEM.BOUNDARY_SETTING":
return "Mehr Grenzsetzung / klare Positionierung."
if m == "MEMA.WITHDRAWAL_SIGNAL":
return "Anzeichen von Rückzug oder geringerer Offenheit."
if m == "CLU.TOPIC_BUDGET_TIME":
return "Thema dreht sich um Zeit/Verfügbarkeit/Priorisierung."
if m == "ATO.HESITATION_VOICE":
return "Hörbare Zögerlichkeit (Pausen/Prosodie)."
return "Relevantes Muster erkannt."

apps/backend/app/services/analyzer.py

import hashlib, json
from ..core.registry import MARKERS
from ..core.detectors import embedding as det_embed
from ..core.detectors import dep as det_dep
from ..core.detectors import prosody as det_pros
from ..core.scoring import aggregate, uncertainty
from ..core.interpret import interpret

def \_msg_id(text:str, meta:dict)->str:
s = json.dumps({"t":text,"m":meta}, sort_keys=True).encode("utf-8")
return hashlib.sha1(s).hexdigest()

def analyze_text(text:str, lang:str="de", prosody:dict|None=None, meta:dict|None=None):
prosody = prosody or {}
meta = meta or {}
message_id = \_msg_id(text, meta)
activations = []

    for m in MARKERS:
        evid_items = []
        support = 0
        evid_scores = {}
        # iterate signals
        for sig in m.signals:
            typ = sig.get("type")
            if typ == "embedding_pattern":
                passed, val, ev = det_embed.run(text, sig)
                evid_items.append(ev); evid_scores["embedding"]=val if passed else 0.0
                support += int(passed)
            elif typ == "dep_pattern":
                passed, val, ev = det_dep.run(text, sig)
                evid_items.append(ev); evid_scores["dep"]=val if passed else 0.0
                support += int(passed)
            elif typ == "prosody_feature":
                passed, val, ev = det_pros.run(text, sig, prosody)
                evid_items.append(ev); evid_scores["prosody"]=val if passed else 0.0
                support += int(passed)

        score = aggregate(evid_scores, m.weights)
        if support >= m.min_support and score >= m.threshold:
            activations.append({
                "marker": m.id,
                "family": m.family,
                "score": score,
                "uncertainty": uncertainty([v for v in evid_scores.values() if v is not None]),
                "evidence": evid_items,
                "interpretation": interpret(m.id, score),
                "schema": m.schema
            })

    return {
      "message_id": message_id,
      "contact_id": meta.get("contact_id"),
      "activations": activations
    }

apps/backend/app/.env.example

ENV=dev
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

4. Vier LD‑Marker (ein Marker je Familie)

marker_registry/LD-3.5/SEM/SEM_BOUNDARY_SETTING.yaml

id: SEM.BOUNDARY_SETTING
ld_schema: "LD-3.5"
family: SEM
lang: de
signals:

- type: embedding_pattern
  encoder: sentence-transformers/all-MiniLM-L6-v2
  positives:
  - "ich brauche klare grenzen"
  - "so nicht mehr"
  - "das geht für mich nicht"
    negatives:
  - "grenze der stadt"
  - "grenzenloser spaß"
    threshold: 0.20 # eff (pos-neg) im [0..1], bewusst moderat fürs MVP
- type: dep_pattern
  pattern: { head_lemma: "setzen", dep: "obj", token_lemma: "grenze" }
  evidence:
  min_support: 1
  weights: { embedding: 0.6, dep: 0.5 }
  threshold: 0.60

marker_registry/LD-3.5/MEMA/MEMA_WITHDRAWAL_SIGNAL.yaml

id: MEMA.WITHDRAWAL_SIGNAL
ld_schema: "LD-3.5"
family: MEMA
lang: de
signals:

- type: embedding_pattern
  encoder: sentence-transformers/all-MiniLM-L6-v2
  positives: - "ich melde mich später" - "gerade keine zeit für das" - "will nicht darüber reden" - "lass das thema"
  negatives: ["zeitmanagement", "später möglich?"]
  threshold: 0.18
  evidence:
  min_support: 1
  weights: { embedding: 1.0 }
  threshold: 0.58

marker_registry/LD-3.5/CLU/CLU_TOPIC_BUDGET_TIME.yaml

id: CLU.TOPIC_BUDGET_TIME
ld_schema: "LD-3.5"
family: CLU
lang: de
signals:

- type: embedding_pattern
  encoder: sentence-transformers/all-MiniLM-L6-v2
  positives: - "zeitplan", "termin", "deadline", "wann passt es", "bin verfügbar", "zeit budget" - "ich habe nur wenig zeit", "heute keine kapazität"
  negatives: ["zeitgeist", "zeitung"]
  threshold: 0.17
  evidence:
  min_support: 1
  weights: { embedding: 1.0 }
  threshold: 0.55

marker_registry/LD-3.5/ATO/ATO_HESITATION_VOICE.yaml

id: ATO.HESITATION_VOICE
ld_schema: "LD-3.5"
family: ATO
lang: de
signals:

- type: prosody_feature
  feature: "pause_ms"
  op: ">"
  threshold: 600
  evidence:
  min_support: 1
  weights: { prosody: 1.0 }
  threshold: 0.60

5. Hilfsskripte

scripts/setup_spacy_de.sh

#!/usr/bin/env bash
set -e
python -m spacy download de_core_news_md
echo "[OK] spaCy de_core_news_md installiert."

scripts/seed_examples.sh (optional)

#!/usr/bin/env bash
curl -s localhost:8000/analyze/text -H "Content-Type: application/json" -d '{
"text":"Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um.",
"meta":{"contact_id":"wa:+4917"}
}' | jq

6. Frontend – schlank, menschenlesbar

apps/frontend/package.json

{
"name": "smirror-frontend",
"private": true,
"version": "0.1.0",
"scripts": {
"dev": "vite",
"build": "vite build",
"preview": "vite preview"
},
"dependencies": {
"react": "^18.2.0",
"react-dom": "^18.2.0"
},
"devDependencies": {
"typescript": "^5.4.0",
"vite": "^5.3.0",
"@types/react": "^18.2.66",
"@types/react-dom": "^18.2.22"
}
}

apps/frontend/index.html

<!doctype html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0" />
    <title>Social Mirror – Marker Probe Panel</title>
    <style>
      body { font-family: Inter, system-ui, sans-serif; margin: 2rem; color:#111;}
      .card { border:1px solid #eee; border-radius:12px; padding:16px; margin-top:12px; }
      .chips span { display:inline-block; padding:4px 8px; margin:4px; border-radius:999px; background:#f3f4f6; font-size:12px;}
      .row { display:flex; align-items:center; gap:12px; }
      .score { width:180px; height:10px; background:#eee; border-radius:6px; overflow:hidden;}
      .score > div { height:10px; }
      .hot { background:linear-gradient(90deg,#f59e0b,#ef4444);}
      .warm { background:#f59e0b;}
      .cool { background:#10b981;}
      .muted { color:#6b7280; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>

apps/frontend/src/main.tsx

import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
createRoot(document.getElementById("root")!).render(<App />);

apps/frontend/src/components/ScoreBar.tsx

import React from "react";
export default function ScoreBar({score}:{score:number}) {
const pct = Math.round(score\*100);
const cls = score>=0.75 ? "hot" : score>=0.6 ? "warm" : "cool";
return (
<div className="score" title={`${pct}%`}>
<div className={cls} style={{width:`${pct}%`}} />
</div>
);
}

apps/frontend/src/components/EvidenceChips.tsx

import React from "react";
type Ev = {type:string, detail:string, span?:string|null}
export default function EvidenceChips({ev}:{ev:Ev[]}) {
return <div className="chips">
{ev.map((e,i)=>(
<span key={i} title={e.type}>
{e.span ? `„${e.span}” — ` : ""}{e.detail}
</span>
))}

  </div>
}

apps/frontend/src/App.tsx

import React, { useState } from "react";
import ScoreBar from "./components/ScoreBar";
import EvidenceChips from "./components/EvidenceChips";

type Activation = {
marker:string; family:string; score:number; uncertainty:number;
interpretation:string; schema:string; evidence:{type:string,detail:string,span?:string}[];
};

export default function App(){
const [text,setText]=useState("Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um.");
const [res,setRes]=useState<{activations:Activation[]} | null>(null);
const [loading,setLoading]=useState(false);

async function analyze(){
setLoading(true);
const r = await fetch("http://localhost:8000/analyze/text",{
method:"POST", headers:{"Content-Type":"application/json"},
body: JSON.stringify({text, lang:"de", prosody:{pause_ms:750}})
});
const j = await r.json();
setRes(j); setLoading(false);
}

return (
<div>
<h1>Social Mirror — Marker Probe Panel</h1>
<p className="muted">Gib Text ein, starte Analyse. Ergebnisse: Score, Evidenz, menschenlesbare Deutung.</p>
<textarea style={{width:"100%",height:120}} value={text} onChange={e=>setText(e.target.value)} />
<div style={{marginTop:8}}>
<button onClick={analyze} disabled={loading}>
{loading ? "Analysiere…" : "Analysieren"}
</button>
</div>

      {res?.activations?.map((a,i)=>(
        <div key={i} className="card">
          <div className="row">
            <strong>{a.marker}</strong>
            <span className="muted">{a.family} · {a.schema}</span>
            <ScoreBar score={a.score}/>
            <span>{Math.round(a.score*100)}%</span>
          </div>
          <p style={{margin:"8px 0"}}>{a.interpretation}</p>
          <EvidenceChips ev={a.evidence}/>
          <div className="muted" style={{fontSize:12, marginTop:6}}>
            Unsicherheit: {(a.uncertainty*100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>

);
}

7. Docker & Make (optional, aber praktisch)

docker/Dockerfile.backend

FROM python:3.11-slim
WORKDIR /app
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && python -m spacy download de_core_news_md
COPY apps/backend /app/apps/backend
COPY marker_registry /app/marker_registry
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn","apps.backend.app.main:app","--host","0.0.0.0","--port","8000"]

docker/Dockerfile.frontend

FROM node:20-alpine
WORKDIR /app
COPY apps/frontend/package.json apps/frontend/package-lock.json\* ./
RUN npm i
COPY apps/frontend /app
EXPOSE 5173
CMD ["npm","run","dev","--","--host"]

docker-compose.yml

services:
backend:
build: { context: ., dockerfile: docker/Dockerfile.backend }
ports: ["8000:8000"]
frontend:
build: { context: ., dockerfile: docker/Dockerfile.frontend }
ports: ["5173:5173"]
depends_on: [backend]

Makefile

setup:
\tpython -m venv .venv && . .venv/bin/activate && pip install -r apps/backend/requirements.txt && bash scripts/setup_spacy_de.sh && cd apps/frontend && npm i
run:
\tuvicorn apps.backend.app.main:app --reload --port 8000
dev-frontend:
\tcd apps/frontend && npm run dev

docs/GETTING_STARTED.md (Kurz)

1. Python-Env + spaCy DE:
   pip install -r apps/backend/requirements.txt && bash scripts/setup_spacy_de.sh
2. Backend starten:
   uvicorn apps.backend.app.main:app --reload --port 8000
3. Frontend starten:
   cd apps/frontend && npm run dev
4. Test:
   POST http://localhost:8000/analyze/text {"text":"Ich brauche klare Grenzen."}

5. Womit du sofort validieren kannst

Testaufruf (mit ATO-Prosodie):

curl -s localhost:8000/analyze/text -H "Content-Type: application/json" -d '{
"text":"Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um.",
"prosody":{"pause_ms": 750},
"meta":{"contact_id":"wa:+4917"}
}' | jq

Im Frontend erscheint derselbe Befund mit Scorebar, Evidenz‑Chips und klarer Deutung statt rohem JSON.
