"""Per-project alpha-to-omega progress — contextually-aware gate evaluation.

Routes:
    /progress/           — main overview (organ cards with repo tables)
    /progress/repo/NAME  — single repo detail view
    /progress/gate-stats — gate pass-rate heatmap
    /progress/blockers   — promotion blockers
    /progress/stale      — staleness report
    /progress/api        — full JSON API
    /progress/api/repo/N — single repo JSON
    /progress/api/gates  — gate stats JSON

All computation is delegated to organvm_engine.metrics (gates, organism, views).
This module only handles routing and template rendering.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dashboard.data.loader import load_registry
from organvm_engine.metrics.gates import GATE_ORDER
from organvm_engine.metrics.organism import get_organism, clear_organism_cache
from organvm_engine.metrics.views import (
    project_blockers,
    project_gate_stats,
    project_organism_cli,
    project_progress_api,
)

router = APIRouter(prefix="/progress", tags=["progress"])

def _get_organism(workspace, registry, registry_file):
    """Get the cached SystemOrganism, loading registry if needed."""
    return get_organism(
        registry=registry,
        workspace=workspace,
        ttl=30,
        registry_file=registry_file,
    )


def clear_progress_cache() -> None:
    """Clear the organism cache (backward compat alias)."""
    clear_organism_cache()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def progress_page(request: Request):
    config = request.app.state.path_config
    registry = load_registry(config)
    organism = _get_organism(
        config.workspace_root(),
        registry,
        config.registry_path(),
    )

    organ_summaries = []
    for o in organism.organs:
        organ_summaries.append({
            "id": o.organ_id,
            "name": o.organ_name,
            "repos": sorted(
                [r.to_dict() for r in o.repos],
                key=lambda x: (-x["pct"], -x["score"], x["repo"]),
            ),
            "count": o.count,
            "avg_pct": o.avg_pct,
            "promo_ready": o.promo_ready_count,
            "stale": o.stale_count,
        })

    gate_stats = [gs.to_dict() for gs in organism.gate_stats()]

    return request.app.state.templates.TemplateResponse(
        request,
        name="progress.html",
        context={
            "page_title": "Progress",
            "organs": organ_summaries,
            "total_repos": organism.total_repos,
            "sys_pct": organism.sys_pct,
            "profile_counts": organism.profile_counts(),
            "promo_counts": organism.promo_counts(),
            "lang_counts": organism.lang_counts(),
            "gate_stats": gate_stats,
            "gate_names": GATE_ORDER,
            "total_discs": organism.total_discrepancies(),
            "total_stale": organism.total_stale,
            "total_ready": organism.total_promo_ready,
        },
    )


@router.get("/repo/{repo_name}", response_class=HTMLResponse)
async def progress_repo_detail(request: Request, repo_name: str):
    config = request.app.state.path_config
    registry = load_registry(config)
    organism = _get_organism(
        config.workspace_root(),
        registry,
        config.registry_path(),
    )
    repo = organism.find_repo(repo_name)
    if not repo:
        # Fuzzy match
        for r in organism.all_repos:
            if repo_name.lower() in r.repo.lower():
                repo = r
                break
    if not repo:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            f"Repo '{repo_name}' not found", status_code=404,
        )

    p = repo.to_dict()
    return request.app.state.templates.TemplateResponse(
        request,
        name="progress_detail.html",
        context={
            "page_title": f"Progress: {p['repo']}",
            "project": p,
            "gate_names": GATE_ORDER,
        },
    )


@router.get("/api")
async def progress_api(request: Request):
    config = request.app.state.path_config
    registry = load_registry(config)
    organism = _get_organism(
        config.workspace_root(),
        registry,
        config.registry_path(),
    )
    return project_progress_api(organism)


@router.get("/api/repo/{repo_name}")
async def progress_api_repo(request: Request, repo_name: str):
    config = request.app.state.path_config
    registry = load_registry(config)
    organism = _get_organism(
        config.workspace_root(),
        registry,
        config.registry_path(),
    )
    return project_organism_cli(organism, repo=repo_name)


@router.get("/api/gates")
async def progress_api_gates(request: Request):
    config = request.app.state.path_config
    registry = load_registry(config)
    organism = _get_organism(
        config.workspace_root(),
        registry,
        config.registry_path(),
    )
    return project_gate_stats(organism)


@router.get("/api/blockers")
async def progress_api_blockers(request: Request):
    config = request.app.state.path_config
    registry = load_registry(config)
    organism = _get_organism(
        config.workspace_root(),
        registry,
        config.registry_path(),
    )
    return project_blockers(organism)
