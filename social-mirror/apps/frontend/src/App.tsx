import React, { useState } from "react";
import ScoreBar from "./components/ScoreBar";
import EvidenceChips from "./components/EvidenceChips";

type Evidence = {
  type: string;
  detail: string;
  span?: string;
};

type Activation = {
  marker: string;
  family: string;
  score: number;
  uncertainty: number;
  interpretation: string;
  schema: string;
  evidence: Evidence[];
};

export default function App() {
  const [text, setText] = useState(
    "Ich brauche klare Grenzen. Bitte setzen wir das jetzt so um."
  );
  const [res, setRes] = useState<{ activations: Activation[] } | null>(null);
  const [loading, setLoading] = useState(false);

  async function analyze() {
    setLoading(true);
    const r = await fetch("http://localhost:8000/analyze/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, lang: "de", prosody: { pause_ms: 750 } })
    });
    const j = await r.json();
    setRes(j);
    setLoading(false);
  }

  return (
    <div>
      <h1>Social Mirror — Marker Probe Panel</h1>
      <p className="muted">
        Gib Text ein, starte Analyse. Ergebnisse: Score, Evidenz, menschenlesbare
        Deutung.
      </p>
      <textarea
        style={{ width: "100%", height: 120 }}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div style={{ marginTop: 8 }}>
        <button onClick={analyze} disabled={loading}>
          {loading ? "Analysiere…" : "Analysieren"}
        </button>
      </div>

      {res?.activations?.map((a, i) => (
        <div key={i} className="card">
          <div className="row">
            <strong>{a.marker}</strong>
            <span className="muted">
              {a.family} · {a.schema}
            </span>
            <ScoreBar score={a.score} />
            <span>{Math.round(a.score * 100)}%</span>
          </div>
          <p style={{ margin: "8px 0" }}>{a.interpretation}</p>
          <EvidenceChips ev={a.evidence} />
          <div className="muted" style={{ fontSize: 12, marginTop: 6 }}>
            Unsicherheit: {(a.uncertainty * 100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );
}
