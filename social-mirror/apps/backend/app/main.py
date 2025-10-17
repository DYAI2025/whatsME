from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import analyze, ingest

app = FastAPI(title="SocialMirror HMA", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint for monitoring."""
    return {"status": "ok"}
