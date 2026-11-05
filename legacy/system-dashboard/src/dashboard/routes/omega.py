"""Omega scorecard — system completion criteria tracking."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from organvm_engine.paths import PathConfig

from dashboard.data.loader import load_registry

router = APIRouter(prefix="/omega", tags=["omega"])


def compute_omega_score(
    registry: dict,
    config: PathConfig | None = None,
) -> tuple[list[dict], dict]:
    """Compute Omega criteria scores using the engine's omega module.

    Returns:
        (criteria_list, soak_info) where criteria_list has id/name/met/value
        dicts and soak_info has streak/remaining/snapshots.
    """
    try:
        from organvm_engine.omega.scorecard import evaluate
        soak_dir = config.soak_dir() if config is not None else None
        scorecard = evaluate(registry=registry, soak_dir=soak_dir)
        criteria = [
            {
                "id": f"#{c.id}",
                "name": c.name,
                "met": c.status == "MET",
                "in_progress": c.status == "IN_PROGRESS",
                "value": c.value,
            }
            for c in scorecard.criteria
        ]
        soak_info = {
            "streak": scorecard.soak.streak_days,
            "remaining": scorecard.soak.days_remaining,
            "target": scorecard.soak.target_days,
            "snapshots": scorecard.soak.total_snapshots,
            "incidents": scorecard.soak.critical_incidents,
        }
        return criteria, soak_info
    except Exception:
        # Fallback if engine omega module unavailable
        return _fallback_criteria(registry), {}


def _fallback_criteria(registry: dict) -> list[dict]:
    """Minimal fallback if engine omega is unavailable."""
    return [
        {"id": "#1", "name": "30-day soak test passes", "met": False, "in_progress": True, "value": "Soak running"},
        {"id": "#6", "name": "AI-conductor essay published", "met": True, "in_progress": False, "value": "Essay #9"},
    ]


@router.get("/", response_class=HTMLResponse)
async def omega_page(request: Request):
    config = request.app.state.path_config
    registry = load_registry(config)
    criteria, soak_info = compute_omega_score(registry, config)

    met_count = sum(1 for c in criteria if c["met"])
    total_count = len(criteria)

    return request.app.state.templates.TemplateResponse(
        request,
        name="omega.html",
        context={
            "page_title": "Omega Scorecard",
            "criteria": criteria,
            "met": met_count,
            "total": total_count,
            "pct": int(met_count / total_count * 100) if total_count else 0,
            "soak": soak_info,
        },
    )
