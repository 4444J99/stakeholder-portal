"""Network testament dashboard — external mirror connections."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/network", tags=["network"])


def _load_network_data(config):
    """Load network data from workspace."""
    import contextlib

    from organvm_engine.network.mapper import discover_network_maps
    from organvm_engine.network.metrics import (
        convergence_points,
        mirror_coverage,
        network_density,
    )
    from organvm_engine.network.ledger import ledger_summary
    from organvm_engine.network.query import organ_density

    workspace = config.workspace_dir
    if not workspace or not workspace.is_dir():
        return {
            "maps": [],
            "maps_count": 0,
            "total_mirrors": 0,
            "density": 0.0,
            "coverage": {"technical": 0.0, "parallel": 0.0, "kinship": 0.0},
            "convergences": {},
            "organ_density": {},
            "ledger_summary": {"total_actions": 0, "unique_projects": 0,
                               "by_lens": {}, "by_form": {}, "by_repo": {},
                               "earliest": None, "latest": None},
        }

    pairs = discover_network_maps(workspace)
    maps = [m for _, m in pairs]

    coverage = mirror_coverage(maps)
    convergences = convergence_points(maps)
    density_by_organ = organ_density(maps)
    summary = ledger_summary()

    return {
        "maps": maps,
        "maps_count": len(maps),
        "total_mirrors": sum(m.mirror_count for m in maps),
        "density": network_density(maps, max(len(maps), 1)),
        "coverage": coverage,
        "convergences": convergences,
        "organ_density": density_by_organ,
        "ledger_summary": summary,
    }


@router.get("/", response_class=HTMLResponse)
async def network_page(request: Request):
    config = request.app.state.path_config
    data = _load_network_data(config)

    # Top convergence points
    top_convergences = sorted(
        data["convergences"].items(),
        key=lambda x: -len(x[1]),
    )[:15]

    # Per-organ breakdown
    organ_rows = []
    for organ, counts in sorted(data["organ_density"].items()):
        organ_rows.append({
            "organ": organ,
            "technical": counts.get("technical", 0),
            "parallel": counts.get("parallel", 0),
            "kinship": counts.get("kinship", 0),
            "total": counts.get("total", 0),
        })

    # Repos with most mirrors
    top_repos = sorted(data["maps"], key=lambda m: -m.mirror_count)[:15]

    return request.app.state.templates.TemplateResponse(
        request,
        name="network.html",
        context={
            "page_title": "Network Testament",
            "maps_count": data["maps_count"],
            "total_mirrors": data["total_mirrors"],
            "density": data["density"],
            "coverage": data["coverage"],
            "top_convergences": top_convergences,
            "organ_rows": organ_rows,
            "top_repos": top_repos,
            "ledger": data["ledger_summary"],
        },
    )


@router.get("/api")
async def network_api(request: Request):
    """JSON network status endpoint."""
    config = request.app.state.path_config
    data = _load_network_data(config)
    return {
        "maps_count": data["maps_count"],
        "total_mirrors": data["total_mirrors"],
        "density": round(data["density"], 3),
        "coverage": {k: round(v, 3) for k, v in data["coverage"].items()},
        "convergence_count": len(data["convergences"]),
        "organ_density": data["organ_density"],
        "ledger": data["ledger_summary"],
    }
