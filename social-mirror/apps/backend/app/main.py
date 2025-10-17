from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from .routes import analyze, ingest

app = FastAPI(title="SocialMirror HMA", version="0.1.0")

# Read allowed origins from environment variable, default to '*' for development
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint for monitoring."""
    return {"status": "ok"}
