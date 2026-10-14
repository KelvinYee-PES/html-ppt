"""FastAPI application root for htmlppt."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from htmlppt.api.routes_brands import router as brands_router
from htmlppt.api.routes_jobs import router as jobs_router
from htmlppt.api.routes_presets import router as presets_router

app = FastAPI(
    title="HTML to PowerPoint API",
    version="0.1.0",
    description="Enterprise-grade HTML to PPTX converter with brand extraction and native shape output.",
)

# Enable CORS for local Vite dev server and production frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(presets_router)
app.include_router(brands_router)
app.include_router(jobs_router)

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


# Mount frontend build if available
frontend_dist = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))
