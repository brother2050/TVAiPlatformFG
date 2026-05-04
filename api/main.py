"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.config import settings
from api.models.base import close_db, init_db
from api.routers import projects, characters, scripts, templates, settings as settings_router, production, editor, media, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle."""
    # Startup
    try:
        await init_db()
        print("✅ Database connected")
    except Exception as e:
        print(f"⚠️  Database not available: {e}")
        print("   API will start without database (some endpoints will fail)")
    # Ensure storage directory exists
    storage_path = Path(settings.storage.local_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    (storage_path / "media").mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    try:
        await close_db()
    except Exception:
        pass


app = FastAPI(
    title="TVAiPlatform API",
    version="0.1.0",
    description="AI-Powered Short Drama Production Platform Backend",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.server.web_port}",
        f"http://127.0.0.1:{settings.server.web_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ────────────────────────────────────────────────────────

app.include_router(projects.router)
app.include_router(characters.router)
app.include_router(scripts.router)
app.include_router(templates.router)
app.include_router(settings_router.router)
app.include_router(production.router)
app.include_router(editor.router)
app.include_router(media.router)
app.include_router(health.router)

# ── Static Files ────────────────────────────────────────────────────────────

media_dir = Path(settings.storage.local_path) / "media"
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/media", StaticFiles(directory=str(media_dir)), name="media")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.server.host,
        port=settings.server.api_port,
        reload=True,
    )
