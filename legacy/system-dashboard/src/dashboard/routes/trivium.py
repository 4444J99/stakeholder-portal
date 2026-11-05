"""Trivium dashboard — Dialectica Universalis visualization."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/trivium", tags=["trivium"])


def _load_trivium_data():
    """Load trivium data from engine."""
    try:
        from organvm_engine.trivium.sources import dialect_data, isomorphism_data
        from organvm_engine.trivium.taxonomy import (
            TranslationTier,
            all_pairs,
            pairs_by_tier,
        )
        from organvm_engine.trivium.dialects import organ_for_dialect

        d_data = dialect_data()
        tier_counts = {
            tier.value: len(pairs_by_tier(tier))
            for tier in TranslationTier
        }

        # Build pair rows for the matrix
        pairs = all_pairs()
        pair_rows = []
        for p in pairs:
            pair_rows.append({
                "source": organ_for_dialect(p.source),
                "target": organ_for_dialect(p.target),
                "tier": p.tier.value,
                "preservation": p.preservation.name.lower(),
                "description": p.description,
                "evidence": p.evidence,
            })

        return {
            "dialects": d_data["dialects"],
            "dialect_count": d_data["count"],
            "tier_counts": tier_counts,
            "pairs": pair_rows,
            "pair_count": len(pair_rows),
            "error": None,
        }
    except Exception as exc:
        return {
            "dialects": [],
            "dialect_count": 0,
            "tier_counts": {},
            "pairs": [],
            "pair_count": 0,
            "error": str(exc),
        }


@router.get("/", response_class=HTMLResponse)
async def trivium_page(request: Request):
    data = _load_trivium_data()

    # Tier color mapping for the matrix
    tier_colors = {
        "formal": "#00ffff",
        "structural": "#ff00ff",
        "analogical": "#ffff00",
        "emergent": "#333333",
    }

    return request.app.state.templates.TemplateResponse(
        request,
        name="trivium.html",
        context={
            "page_title": "Trivium — Dialectica Universalis",
            "dialects": data["dialects"],
            "dialect_count": data["dialect_count"],
            "tier_counts": data["tier_counts"],
            "pairs": data["pairs"],
            "pair_count": data["pair_count"],
            "tier_colors": tier_colors,
            "error": data["error"],
        },
    )
