"""IRF dashboard — Index Rerum Faciendarum item browser."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/irf", tags=["irf"])


def _load_irf_data() -> dict:
    """Load and summarise IRF data from the engine."""
    try:
        from organvm_engine.irf import irf_stats, parse_irf, query_irf
        from organvm_engine.paths import irf_path

        items = parse_irf(irf_path())
        stats = irf_stats(items)
        open_items = query_irf(items, status="open")
        p0_items = query_irf(items, priority="P0", status="open")
        completed_items = query_irf(items, status="completed")

        return {
            "stats": stats,
            "open_items": open_items,
            "p0_items": p0_items,
            "completed_items": completed_items,
            "error": None,
        }
    except Exception as exc:
        return {
            "stats": {
                "total": 0,
                "open": 0,
                "completed": 0,
                "blocked": 0,
                "archived": 0,
                "completion_rate": 0.0,
                "by_priority": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
                "by_domain": {},
            },
            "open_items": [],
            "p0_items": [],
            "completed_items": [],
            "error": str(exc),
        }


@router.get("/", response_class=HTMLResponse)
async def irf_page(request: Request):
    data = _load_irf_data()
    stats = data["stats"]

    completion_pct = int(stats["completion_rate"] * 100)

    return request.app.state.templates.TemplateResponse(
        request,
        name="irf.html",
        context={
            "page_title": "IRF — Index Rerum Faciendarum",
            "stats": stats,
            "completion_pct": completion_pct,
            "open_items": data["open_items"],
            "p0_items": data["p0_items"],
            "completed_items": data["completed_items"],
            "error": data["error"],
        },
    )
