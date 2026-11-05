"""System pulse — mood, density, events, nerve wiring, flow."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/pulse", tags=["pulse"])


def _sparkline_svg(values: list[float], width: int = 200, height: int = 40) -> str:
    """Generate an inline SVG sparkline polyline from a list of floats."""
    if not values or len(values) < 2:
        return ""
    lo = min(values)
    hi = max(values)
    span = hi - lo if hi > lo else 1.0

    points: list[str] = []
    for i, v in enumerate(values):
        x = round(i / (len(values) - 1) * width, 1)
        y = round(height - (v - lo) / span * height, 1)
        points.append(f"{x},{y}")

    polyline = " ".join(points)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{polyline}" fill="none" stroke="#00F" '
        f'stroke-width="2" stroke-linejoin="round"/>'
        f"</svg>"
    )


def _load_pulse_data(config) -> dict:
    """Compute all pulse data from organvm-engine.

    Returns a dict with mood, density, events, nerve, and cross-organ data.
    Falls back gracefully if the pulse module is not available.
    """
    from organvm_engine.pulse.affective import MoodFactors, compute_mood
    from organvm_engine.pulse.density import compute_density
    from organvm_engine.pulse.events import event_counts, recent
    from organvm_engine.pulse.nerve import resolve_subscriptions
    from organvm_engine.metrics.organism import get_organism
    from organvm_engine.seed.graph import build_seed_graph, validate_edge_resolution

    workspace = config.workspace_root()
    organism = get_organism(include_omega=False)

    # Seed graph + density
    graph = build_seed_graph(workspace)
    unresolved = validate_edge_resolution(graph)
    dp = compute_density(graph, organism, len(unresolved))

    # Mood factors from organism + density
    total = organism.total_repos or 1
    gate_stats = organism.gate_stats()
    avg_gate_rate = (
        sum(g.rate for g in gate_stats) / len(gate_stats) if gate_stats else 0.0
    )

    factors = MoodFactors(
        health_pct=organism.sys_pct,
        health_velocity=0.0,
        stale_ratio=organism.total_stale / total,
        stale_velocity=0.0,
        density_score=dp.interconnection_score,
        gate_pass_rate=avg_gate_rate,
        promo_ready_ratio=organism.total_promo_ready / total,
        session_frequency=0.0,
    )

    mood_result = compute_mood(factors)
    recent_events = recent(10)
    counts = event_counts()

    # Nerve subscriptions
    bundle = resolve_subscriptions(workspace)

    # Cross-organ edges from graph
    outbound_orgs: set[str] = set()
    inbound_orgs: set[str] = set()
    cross_count = 0
    for src, tgt, _ in graph.edges:
        src_org = src.split("/", maxsplit=1)[0] if "/" in src else src
        tgt_org = tgt.split("/", maxsplit=1)[0] if "/" in tgt else tgt
        if src_org != tgt_org:
            cross_count += 1
            outbound_orgs.add(src_org)
            inbound_orgs.add(tgt_org)

    # AMMOI density snapshot (best-effort)
    ammoi = None
    try:
        from organvm_engine.pulse.ammoi import compute_ammoi

        ammoi = compute_ammoi(workspace=workspace, include_events=True)
    except Exception:
        pass

    # Inference tensions + advisories (best-effort)
    inference = None
    try:
        from organvm_engine.pulse.inference_bridge import run_inference

        inference = run_inference(workspace)
    except Exception:
        pass

    # Structural edges from ontologia (best-effort)
    edge_summary = {"hierarchy": 0, "relations": 0, "cross_organ": 0, "by_type": {}}
    try:
        from ontologia.registry.store import open_store as _edge_open_store

        _edge_store = _edge_open_store()
        _ei = _edge_store.edge_index
        _h_edges = [e for e in _ei.all_hierarchy_edges() if e.is_active()]
        _r_edges = [e for e in _ei.all_relation_edges() if e.is_active()]
        _by_type: dict[str, int] = {}
        for _e in _r_edges:
            _by_type[_e.relation_type] = _by_type.get(_e.relation_type, 0) + 1

        # Cross-organ via hierarchy parent mapping
        _c2o: dict[str, str] = {}
        for _e in _h_edges:
            _c2o[_e.child_id] = _e.parent_id
        _cross = sum(
            1 for _e in _r_edges
            if _c2o.get(_e.source_id, "") and _c2o.get(_e.target_id, "")
            and _c2o[_e.source_id] != _c2o[_e.target_id]
        )
        edge_summary = {
            "hierarchy": len(_h_edges),
            "relations": len(_r_edges),
            "cross_organ": _cross,
            "by_type": _by_type,
        }
    except Exception:
        pass

    advisories_list = []
    try:
        from organvm_engine.pulse.advisories import read_advisories

        advisories_list = read_advisories(limit=10, unacked_only=True)
    except Exception:
        pass

    # Temporal profile from AMMOI history (best-effort)
    temporal_data: dict | None = None
    density_sparkline: list[float] = []
    try:
        from organvm_engine.pulse.ammoi import _read_history, extract_timeseries
        from organvm_engine.pulse.temporal import compute_temporal_profile

        history = _read_history(limit=50)
        if len(history) >= 3:
            timeseries = extract_timeseries(history)
            profile = compute_temporal_profile(timeseries)
            temporal_data = profile.to_dict()
            density_sparkline = timeseries.get("system_density", [])
    except Exception:
        pass

    return {
        "mood": mood_result,
        "density": dp,
        "events": recent_events,
        "event_counts": counts,
        "nerve": bundle,
        "cross_organ_edges": cross_count,
        "outbound_orgs": sorted(outbound_orgs),
        "inbound_orgs": sorted(inbound_orgs),
        "total_edges": len(graph.edges),
        "total_nodes": len(graph.nodes),
        "organism_sys_pct": organism.sys_pct,
        "organism_total_repos": organism.total_repos,
        "ammoi": ammoi,
        "inference": inference,
        "advisories": advisories_list,
        "edge_summary": edge_summary,
        "temporal": temporal_data,
        "density_sparkline": density_sparkline,
    }


def _fallback_data() -> dict:
    """Return empty/safe data when pulse module is unavailable."""
    return {
        "mood": None,
        "density": None,
        "events": [],
        "event_counts": {},
        "nerve": None,
        "cross_organ_edges": 0,
        "outbound_orgs": [],
        "inbound_orgs": [],
        "total_edges": 0,
        "total_nodes": 0,
        "organism_sys_pct": 0,
        "organism_total_repos": 0,
        "ammoi": None,
        "error": "Pulse module unavailable",
    }


@router.get("/", response_class=HTMLResponse)
async def pulse_page(request: Request):
    config = request.app.state.path_config

    try:
        data = _load_pulse_data(config)
    except Exception:
        data = _fallback_data()

    mood = data["mood"]
    density = data["density"]
    nerve = data["nerve"]

    # Build nerve summary for template
    nerve_summary: list[dict] = []
    if nerve is not None:
        for etype in sorted(nerve.by_event.keys()):
            subs = nerve.by_event[etype]
            subscribers = [
                {"name": s.subscriber, "action": s.action} for s in subs
            ]
            nerve_summary.append({
                "event_type": etype,
                "count": len(subs),
                "subscribers": subscribers,
            })

    # Build event rows
    event_rows: list[dict] = []
    for evt in data["events"]:
        ts = evt.timestamp[:19] if len(evt.timestamp) >= 19 else evt.timestamp
        event_rows.append({
            "timestamp": ts,
            "event_type": evt.event_type,
            "source": evt.source,
        })

    # Coverage bars from density
    coverage_bars: list[dict] = []
    if density is not None:
        total = density.total_repos or 1
        coverage_bars = [
            {
                "label": "Seeds",
                "count": density.repos_with_seeds,
                "total": density.total_repos,
                "pct": round(density.repos_with_seeds / total * 100, 1),
            },
            {
                "label": "CI",
                "count": density.repos_with_ci,
                "total": density.total_repos,
                "pct": round(density.repos_with_ci / total * 100, 1),
            },
            {
                "label": "Tests",
                "count": density.repos_with_tests,
                "total": density.total_repos,
                "pct": round(density.repos_with_tests / total * 100, 1),
            },
            {
                "label": "Docs",
                "count": density.repos_with_docs,
                "total": density.total_repos,
                "pct": round(density.repos_with_docs / total * 100, 1),
            },
        ]

    # Build tension rows
    inference = data.get("inference")
    tension_rows: list[dict] = []
    if inference is not None:
        for t in inference.tensions:
            tension_rows.append({
                "type": t.get("type", "unknown"),
                "severity": t.get("severity", 0.0),
                "description": t.get("description", ""),
            })

    # Build advisory rows
    advisory_rows: list[dict] = []
    for adv in data.get("advisories", []):
        advisory_rows.append({
            "id": adv.advisory_id,
            "severity": adv.severity,
            "action": adv.action,
            "entity": adv.entity_name,
            "description": adv.description,
        })

    return request.app.state.templates.TemplateResponse(
        request,
        name="pulse.html",
        context={
            "page_title": "Pulse",
            "mood": mood,
            "density": density,
            "event_rows": event_rows,
            "nerve_summary": nerve_summary,
            "coverage_bars": coverage_bars,
            "cross_organ_edges": data["cross_organ_edges"],
            "outbound_orgs": data["outbound_orgs"],
            "inbound_orgs": data["inbound_orgs"],
            "total_edges": data["total_edges"],
            "total_nodes": data["total_nodes"],
            "event_counts": data["event_counts"],
            "error": data.get("error"),
            "ammoi": data.get("ammoi"),
            "tension_rows": tension_rows,
            "advisory_rows": advisory_rows,
            "inference_score": inference.inference_score if inference else 0.0,
            "tension_count": inference.tension_count if inference else 0,
            "cluster_count": inference.cluster_count if inference else 0,
            "edge_summary": data.get("edge_summary", {}),
            "temporal": data.get("temporal"),
            "density_sparkline_svg": _sparkline_svg(data.get("density_sparkline", [])),
        },
    )


@router.get("/api")
async def pulse_api(request: Request):
    """JSON endpoint returning all pulse data."""
    config = request.app.state.path_config

    try:
        data = _load_pulse_data(config)
    except Exception:
        data = _fallback_data()
        return data

    mood = data["mood"]
    density = data["density"]
    nerve = data["nerve"]

    ammoi = data.get("ammoi")

    return {
        "mood": mood.to_dict() if mood else None,
        "density": density.to_dict() if density else None,
        "events": [
            {
                "timestamp": e.timestamp,
                "event_type": e.event_type,
                "source": e.source,
            }
            for e in data["events"]
        ],
        "event_counts": data["event_counts"],
        "nerve_total": len(nerve.subscriptions) if nerve else 0,
        "nerve_event_types": len(nerve.by_event) if nerve else 0,
        "cross_organ_edges": data["cross_organ_edges"],
        "total_edges": data["total_edges"],
        "total_nodes": data["total_nodes"],
        "ammoi": ammoi.to_dict() if ammoi else None,
        "inference": data["inference"].to_dict() if data.get("inference") is not None else None,
        "advisories": [a.to_dict() for a in data.get("advisories", [])],
        "edge_summary": data.get("edge_summary", {}),
        "temporal": data.get("temporal"),
    }


@router.get("/events", response_class=HTMLResponse)
async def pulse_events(request: Request):
    """HTMX partial returning the recent events table rows."""
    config = request.app.state.path_config

    try:
        from organvm_engine.pulse.events import recent

        events = recent(20)
    except Exception:
        events = []

    rows: list[dict] = []
    for evt in events:
        ts = evt.timestamp[:19] if len(evt.timestamp) >= 19 else evt.timestamp
        rows.append({
            "timestamp": ts,
            "event_type": evt.event_type,
            "source": evt.source,
        })

    return request.app.state.templates.TemplateResponse(
        request,
        name="pulse_events_partial.html",
        context={"event_rows": rows},
    )


@router.get("/history")
async def pulse_history(request: Request):
    """JSON endpoint returning AMMOI history for temporal charts."""
    days = int(request.query_params.get("days", "30"))

    try:
        from organvm_engine.pulse.rhythm import pulse_history as get_history

        snapshots = get_history(days=days)
    except Exception:
        snapshots = []

    return {
        "days": days,
        "count": len(snapshots),
        "snapshots": snapshots,
    }
