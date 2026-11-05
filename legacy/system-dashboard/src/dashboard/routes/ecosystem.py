"""Ecosystem health endpoint + page."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ecosystem", tags=["ecosystem"])


def _load_ecosystem_data(config):
    """Load ecosystem data from workspace using organvm-engine."""
    import contextlib

    from organvm_engine.ecosystem.discover import discover_ecosystems
    from organvm_engine.ecosystem.query import coverage_matrix, next_actions, status_summary
    from organvm_engine.ecosystem.reader import read_ecosystem

    workspace = config.workspace
    paths = discover_ecosystems(workspace)
    ecosystems: list[dict] = []
    for p in paths:
        with contextlib.suppress(Exception):
            ecosystems.append(read_ecosystem(p))

    matrix = coverage_matrix(ecosystems)
    actions = next_actions(ecosystems)
    summary = status_summary(ecosystems)

    return {
        "ecosystems": ecosystems,
        "matrix": matrix,
        "actions": actions,
        "summary": summary,
        "total_products": len(ecosystems),
    }


@router.get("/", response_class=HTMLResponse)
async def ecosystem_page(request: Request):
    config = request.app.state.path_config
    data = _load_ecosystem_data(config)

    # Collect all pillar names for table header
    all_pillars: set[str] = set()
    for repo_data in data["matrix"].values():
        all_pillars.update(repo_data.keys())
    pillars = sorted(all_pillars)

    # Build heatmap rows
    heatmap: list[dict] = []
    for repo, coverage in sorted(data["matrix"].items()):
        row = {"repo": repo, "pillars": {}}
        for p in pillars:
            if p in coverage:
                total = coverage[p].get("total", 0)
                live = coverage[p].get("live", 0)
                row["pillars"][p] = {"total": total, "live": live}
            else:
                row["pillars"][p] = None
        heatmap.append(row)

    # Status distribution
    summary = data["summary"]

    # Top 10 actions
    top_actions = data["actions"][:10]

    return request.app.state.templates.TemplateResponse(
        request,
        name="ecosystem.html",
        context={
            "page_title": "Ecosystem",
            "total_products": data["total_products"],
            "pillars": pillars,
            "heatmap": heatmap,
            "summary": summary,
            "actions": top_actions,
        },
    )


@router.get("/api")
async def ecosystem_api(request: Request):
    """JSON ecosystem data endpoint."""
    config = request.app.state.path_config
    data = _load_ecosystem_data(config)
    return {
        "total_products": data["total_products"],
        "matrix": data["matrix"],
        "summary": data["summary"],
        "actions_count": len(data["actions"]),
    }
