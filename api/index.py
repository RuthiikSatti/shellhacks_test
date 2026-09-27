"""Vercel entry point for the ShellHacks full-stack app.

FastAPI serves the backend under /api and the built Vite app everywhere else.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
DIST_DIR = ROOT_DIR / "frontend" / "dist"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.main import app as main_app

app = FastAPI(title="Portfolio Story", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Backend API. Mounting strips the /api prefix before main_app sees the route.
app.mount("/api", main_app)

# Serve Vite's hashed JS/CSS directly from the bundled frontend build.
ASSETS_DIR = DIST_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    """Serve real static files when present, otherwise fall back to the SPA."""
    if not DIST_DIR.exists():
        raise HTTPException(status_code=500, detail="Frontend build was not bundled.")

    requested = (DIST_DIR / path).resolve()
    dist_root = DIST_DIR.resolve()

    # Do not allow ../ traversal outside frontend/dist.
    if requested.is_file() and (requested == dist_root or dist_root in requested.parents):
        return FileResponse(requested)

    index_file = DIST_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    raise HTTPException(status_code=500, detail="Frontend index.html is missing.")
