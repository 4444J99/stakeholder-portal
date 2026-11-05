"""Testament gallery — the system's generative self-portrait."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/testament", tags=["testament"])

ARTIFACTS_DIR = Path.home() / ".organvm" / "testament" / "artifacts"


@router.get("/", response_class=HTMLResponse)
async def testament_gallery():
    """Serve the testament gallery page, or generate it on the fly."""
    gallery_path = ARTIFACTS_DIR / "index.html"
    if gallery_path.exists():
        return HTMLResponse(gallery_path.read_text())

    # Generate inline if no gallery exists yet
    from organvm_engine.testament.catalog import load_catalog
    from organvm_engine.testament.renderers.html import render_gallery_page

    catalog = load_catalog()
    art_dicts = []
    for a in catalog:
        mod = a.modality.value if hasattr(a.modality, "value") else str(a.modality)
        fmt = a.format.value if hasattr(a.format, "value") else str(a.format)
        art_dicts.append({
            "title": a.title,
            "modality": mod,
            "format": fmt,
            "path": Path(a.path).name if a.path else "",
            "timestamp": a.timestamp,
            "organ": a.organ or "system",
        })

    html = render_gallery_page(art_dicts)
    return HTMLResponse(html)


@router.get("/artifact/{filename}")
async def testament_artifact(filename: str):
    """Serve a specific testament artifact file."""
    from fastapi.responses import FileResponse, Response

    artifact_path = ARTIFACTS_DIR / filename

    # Security: only serve from artifacts dir, no path traversal
    try:
        artifact_path = artifact_path.resolve()
        if not str(artifact_path).startswith(str(ARTIFACTS_DIR.resolve())):
            return Response(status_code=404)
    except (ValueError, OSError):
        return Response(status_code=404)

    if not artifact_path.exists():
        return Response(status_code=404)

    suffix = artifact_path.suffix.lower()
    media_types = {
        ".svg": "image/svg+xml",
        ".html": "text/html",
        ".md": "text/markdown",
        ".json": "application/json",
        ".txt": "text/plain",
        ".png": "image/png",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    return FileResponse(artifact_path, media_type=media_type)


@router.get("/status")
async def testament_status():
    """JSON status endpoint for testament system."""
    from organvm_engine.testament.catalog import catalog_summary, load_catalog
    from organvm_engine.testament.manifest import (
        MODULE_SOURCES,
        ORGAN_OUTPUT_MATRIX,
        all_artifact_types,
    )

    types = all_artifact_types()
    catalog = load_catalog()
    summary = catalog_summary(catalog)

    return {
        "registered_types": len(types),
        "organ_profiles": len(ORGAN_OUTPUT_MATRIX),
        "source_modules": len(MODULE_SOURCES),
        "catalog_total": summary.total,
        "by_modality": summary.by_modality,
        "by_organ": summary.by_organ,
        "latest_timestamp": summary.latest_timestamp,
    }
