"""Dependency graph visualization."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from collections import defaultdict

from dashboard.data.loader import load_registry

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/", response_class=HTMLResponse)
async def graph_page(request: Request):
    registry = load_registry(request.app.state.path_config)
    organs = registry.get("organs", {})

    edges = []
    nodes = set()
    cross_organ = defaultdict(int)

    for organ_key, organ_data in organs.items():
        for repo in organ_data.get("repositories", []):
            key = f"{repo['org']}/{repo['name']}"
            nodes.add(key)
            for dep in repo.get("dependencies", []):
                edges.append({"from": key, "to": dep})
                from_org = key.split("/")[0]
                to_org = dep.split("/")[0]
                if from_org != to_org:
                    cross_organ[f"{from_org} → {to_org}"] += 1

    return request.app.state.templates.TemplateResponse(
        request,
        name="graph.html",
        context={
            "page_title": "Dependency Graph",
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "edges": edges,
            "cross_organ": dict(sorted(cross_organ.items())),
        },
    )


@router.get("/api")
async def graph_api(request: Request):
    """Graph data as JSON for visualization."""
    registry = load_registry(request.app.state.path_config)
    nodes = []
    edges = []

    for organ_key, organ_data in registry.get("organs", {}).items():
        for repo in organ_data.get("repositories", []):
            key = f"{repo['org']}/{repo['name']}"
            nodes.append({
                "id": key,
                "organ": organ_key,
                "tier": repo.get("tier", "standard"),
            })
            for dep in repo.get("dependencies", []):
                edges.append({"source": key, "target": dep})

    return {"nodes": nodes, "edges": edges}
