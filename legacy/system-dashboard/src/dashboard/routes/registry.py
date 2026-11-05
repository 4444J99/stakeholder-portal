"""Registry browser."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse

from dashboard.data.loader import load_registry

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/", response_class=HTMLResponse)
async def registry_page(
    request: Request,
    organ: str | None = Query(None),
    status: str | None = Query(None),
    tier: str | None = Query(None),
):
    registry = load_registry(request.app.state.path_config)
    organs = registry.get("organs", {})

    repos = []
    for organ_key, organ_data in organs.items():
        if organ and organ_key != organ:
            continue
        for repo in organ_data.get("repositories", []):
            if status and repo.get("implementation_status") != status:
                continue
            if tier and repo.get("tier") != tier:
                continue
            repos.append({
                "organ": organ_key,
                "name": repo.get("name", "?"),
                "org": repo.get("org", "?"),
                "status": repo.get("implementation_status", "?"),
                "tier": repo.get("tier", "?"),
                "promotion": repo.get("promotion_status", "?"),
                "public": repo.get("public", False),
                "description": repo.get("description", "")[:80],
            })

    organ_keys = sorted(organs.keys())

    return request.app.state.templates.TemplateResponse(
        request,
        name="registry.html",
        context={
            "page_title": "Registry Browser",
            "repos": repos,
            "total": len(repos),
            "organ_keys": organ_keys,
            "filter_organ": organ or "",
            "filter_status": status or "",
            "filter_tier": tier or "",
        },
    )


@router.get("/api/{repo_name}")
async def registry_repo_api(request: Request, repo_name: str):
    """Get single repo details as JSON."""
    registry = load_registry(request.app.state.path_config)
    for organ_key, organ_data in registry.get("organs", {}).items():
        for repo in organ_data.get("repositories", []):
            if repo.get("name") == repo_name:
                return {"organ": organ_key, **repo}
    return {"error": "not found"}
