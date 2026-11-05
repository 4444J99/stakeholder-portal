"""REST API v1 — read-only endpoints wrapping organvm-mcp-server tool functions.

Each endpoint is a thin wrapper: import the tool function, pass query params,
return the dict (FastAPI auto-serializes to JSON). Designed for mobile access
via iOS Shortcuts and Safari through a Cloudflare Tunnel.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from dashboard.formatters.plaintext import format_response
from dashboard.middleware.auth import require_api_auth

router = APIRouter(
    prefix="/api/v1",
    tags=["api-v1"],
    dependencies=[Depends(require_api_auth)],
)


def _negotiate(
    request: Request, endpoint: str, data: dict[str, Any],
) -> dict[str, Any] | PlainTextResponse:
    """Return plain text if client sends Accept: text/plain, else dict (JSON)."""
    accept = request.headers.get("accept", "")
    if "text/plain" in accept:
        return PlainTextResponse(format_response(endpoint, data))
    return data


# ── Health ──────────────────────────────────────────────────────────────


@router.get("/status", response_model=None)
async def api_status(request: Request):
    """System health summary (CLI: organvm status --json)."""
    from organvm_mcp.tools.health import system_health

    return _negotiate(request, "status", system_health())


@router.get("/organism")
async def api_organism(
    organ: str | None = None,
    repo: str | None = None,
    view: str | None = None,
) -> dict[str, Any]:
    """Organism view (CLI: organvm organism)."""
    from organvm_mcp.tools.health import organism

    return organism(organ=organ, repo=repo, view=view or "full")


@router.get("/omega", response_model=None)
async def api_omega(request: Request):
    """Omega scorecard (CLI: organvm omega status)."""
    from organvm_mcp.tools.health import omega_status

    return _negotiate(request, "omega", omega_status())


@router.get("/ci", response_model=None)
async def api_ci(request: Request):
    """CI health (CLI: organvm ci health)."""
    from organvm_mcp.tools.health import ci_health

    return _negotiate(request, "ci", ci_health())


@router.get("/deadlines", response_model=None)
async def api_deadlines(request: Request, days: int = 30):
    """Upcoming deadlines (CLI: organvm deadlines)."""
    from organvm_mcp.tools.health import deadlines

    return _negotiate(request, "deadlines", deadlines(days=days))


@router.get("/pitch")
async def api_pitch() -> dict[str, Any]:
    """Pitch deck status (CLI: organvm pitch sync)."""
    from organvm_mcp.tools.health import pitch_status

    return pitch_status()


# ── Registry ────────────────────────────────────────────────────────────


@router.get("/registry", response_model=None)
async def api_registry(
    request: Request,
    organ: str | None = None,
    tier: str | None = None,
    status: str | None = None,
    name_pattern: str | None = None,
    limit: int = 50,
):
    """Query registry (CLI: organvm registry list)."""
    from organvm_mcp.tools.registry import query_registry

    data = query_registry(
        organ=organ,
        tier=tier,
        promotion_status=status,
        name_pattern=name_pattern,
        limit=limit,
    )
    return _negotiate(request, "registry", data)


@router.get("/registry/{org}/{name}")
async def api_registry_repo(org: str, name: str) -> dict[str, Any]:
    """Get a single repo (CLI: organvm registry show)."""
    from organvm_mcp.tools.registry import get_repo

    return get_repo(org=org, name=name)


@router.get("/organs")
async def api_organs() -> dict[str, Any]:
    """List all organs."""
    from organvm_mcp.tools.registry import list_organs

    return list_organs()


# ── Seeds & Edges ───────────────────────────────────────────────────────


@router.get("/seeds/{org}/{name}")
async def api_seed(org: str, name: str) -> dict[str, Any]:
    """Get seed.yaml for a repo (CLI: organvm seed validate)."""
    from organvm_mcp.tools.seeds import get_seed

    return get_seed(org=org, name=name)


@router.get("/edges")
async def api_edges(
    repo: str | None = None,
    organ: str | None = None,
    direction: str = "both",
) -> dict[str, Any]:
    """Find produces/consumes edges (CLI: organvm seed graph)."""
    from organvm_mcp.tools.seeds import find_edges

    return find_edges(repo=repo, organ=organ, direction=direction)


# ── Graph ───────────────────────────────────────────────────────────────


@router.get("/graph")
async def api_graph(organ: str | None = None) -> dict[str, Any]:
    """Dependency graph (CLI: organvm seed graph)."""
    from organvm_mcp.tools.graph import get_dependency_graph

    return get_dependency_graph(organ=organ)


@router.get("/graph/trace")
async def api_graph_trace(
    repo: str | None = None,
    organ: str | None = None,
    direction: str = "both",
    depth: int = 2,
) -> dict[str, Any]:
    """Trace dependencies (CLI: organvm governance check-deps)."""
    from organvm_mcp.tools.graph import trace_dependencies

    return trace_dependencies(repo=repo, organ=organ, direction=direction, depth=depth)


# ── Governance ──────────────────────────────────────────────────────────


@router.get("/governance/audit", response_model=None)
async def api_governance_audit(request: Request):
    """Governance audit (CLI: organvm governance audit)."""
    from organvm_mcp.tools.governance import governance_audit

    return _negotiate(request, "governance_audit", governance_audit())


@router.get("/governance/impact/{repo}")
async def api_governance_impact(repo: str) -> dict[str, Any]:
    """Blast-radius impact for a repo (CLI: organvm governance impact)."""
    from organvm_mcp.tools.governance import governance_impact

    return governance_impact(repo_name=repo)


# ── Metrics ─────────────────────────────────────────────────────────────


@router.get("/metrics")
async def api_metrics() -> dict[str, Any]:
    """Compute system metrics (CLI: organvm metrics calculate)."""
    from organvm_mcp.tools.metrics import metrics_compute

    return metrics_compute()


# ── Ecosystem ───────────────────────────────────────────────────────────


@router.get("/ecosystem/{product}")
async def api_ecosystem(product: str) -> dict[str, Any]:
    """Ecosystem profile for a product (CLI: organvm ecosystem show)."""
    from organvm_mcp.tools.ecosystem import ecosystem_profile

    return ecosystem_profile(repo=product)


# ── Coordination ────────────────────────────────────────────────────────


@router.get("/coordination/board", response_model=None)
async def api_coordination_board(request: Request):
    """Multi-agent work board."""
    from organvm_mcp.tools.coordination import coordination_work_board

    return _negotiate(request, "coordination_board", coordination_work_board())
