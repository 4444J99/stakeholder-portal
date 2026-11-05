"""Soak test trends."""

from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from dashboard.data.loader import load_soak_snapshots

router = APIRouter(prefix="/soak", tags=["soak"])

VIGILIA_START = datetime(2026, 2, 16, tzinfo=timezone.utc)
VIGILIA_DAYS = 30


@router.get("/", response_class=HTMLResponse)
async def soak_page(request: Request):
    snapshots = load_soak_snapshots(request.app.state.path_config)

    # VIGILIA timer
    now = datetime.now(timezone.utc)
    elapsed = (now - VIGILIA_START).days
    remaining = max(0, VIGILIA_DAYS - elapsed)
    pct = min(100, int(elapsed / VIGILIA_DAYS * 100))

    # CI trend
    ci_trend = []
    for snap in snapshots:
        ci = snap.get("ci", {})
        total = ci.get("total_checked", 0)
        passing = ci.get("passing", 0)
        rate = round(passing / total * 100, 1) if total > 0 else 0.0
        ci_trend.append({
            "date": snap.get("date", "?"),
            "passing": passing,
            "failing": ci.get("failing", 0),
            "total": total,
            "rate": rate,
        })

    # Latest snapshot
    latest = snapshots[-1] if snapshots else {}

    return request.app.state.templates.TemplateResponse(
        request,
        name="soak.html",
        context={
            "page_title": "Soak Test (VIGILIA)",
            "elapsed": elapsed,
            "remaining": remaining,
            "pct": pct,
            "total_snapshots": len(snapshots),
            "ci_trend": ci_trend,
            "latest": latest,
        },
    )
