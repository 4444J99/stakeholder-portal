"""System health endpoint + page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dashboard.data.loader import load_registry, load_metrics, organ_summary

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_class=HTMLResponse)
async def health_page(request: Request):
    config = request.app.state.path_config
    registry = load_registry(config)
    metrics = load_metrics(config)
    organs = organ_summary(registry)

    computed = metrics.get("computed", {})
    manual = metrics.get("manual", {})

    return request.app.state.templates.TemplateResponse(
        request,
        name="health.html",
        context={
            "page_title": "System Health",
            "organs": organs,
            "total_repos": computed.get("total_repos", 0),
            "active_repos": computed.get("active_repos", 0),
            "archived_repos": computed.get("archived_repos", 0),
            "ci_workflows": computed.get("ci_workflows", 0),
            "dep_edges": computed.get("dependency_edges", 0),
            "essays": computed.get("published_essays", 0),
            "sprints": computed.get("sprints_completed", 0),
            "total_words": manual.get("total_words_short", "?"),
        },
    )


@router.get("/api")
async def health_api(request: Request):
    """JSON health check endpoint."""
    config = request.app.state.path_config
    registry = load_registry(config)
    metrics = load_metrics(config)
    organs = organ_summary(registry)

    all_operational = all(o["status"] == "OPERATIONAL" for o in organs)

    return {
        "status": "healthy" if all_operational else "degraded",
        "organs": len(organs),
        "all_operational": all_operational,
        "total_repos": metrics.get("computed", {}).get("total_repos", 0),
    }
