"""Atoms pipeline dashboard — per-organ task/prompt visualization."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from organvm_engine.paths import PathConfig

from dashboard.data.loader import load_atom_rollups

router = APIRouter(prefix="/atoms", tags=["atoms"])


@router.get("/", response_class=HTMLResponse)
async def atoms_page(request: Request):
    config = request.app.state.path_config
    rollups = load_atom_rollups(config)

    # Build per-organ summary rows
    organs = []
    total_tasks = 0
    total_pending = 0
    total_prompts = 0
    total_xlinks = 0
    all_fingerprints: dict[str, int] = {}
    link_matrix: dict[str, dict[str, int]] = {}

    for key in sorted(rollups):
        r = rollups[key]
        tasks = r.get("total_tasks", 0)
        pending = r.get("pending_tasks", 0)
        completed = r.get("completed_tasks", 0)
        prompt_dist = r.get("prompt_type_dist", {})
        prompts = sum(prompt_dist.values())
        xlinks = len(r.get("cross_organ_links", []))

        total_tasks += tasks
        total_pending += pending
        total_prompts += prompts
        total_xlinks += xlinks

        organs.append({
            "key": key,
            "dir": r.get("organ_dir", ""),
            "tasks": tasks,
            "pending": pending,
            "completed": completed,
            "prompts": prompts,
            "xlinks": xlinks,
            "prompt_dist": prompt_dist,
            "pending_by_repo": r.get("pending_by_repo", {}),
        })

        # Aggregate fingerprints
        for fp, count in r.get("domain_fingerprints", {}).items():
            all_fingerprints[fp] = all_fingerprints.get(fp, 0) + count

        # Build link matrix
        for link in r.get("cross_organ_links", []):
            src = link.get("task_organ", "?")
            dst = link.get("prompt_organ", "?")
            link_matrix.setdefault(src, {})
            link_matrix[src][dst] = link_matrix[src].get(dst, 0) + 1

    # Top fingerprints (excluding empty)
    top_fps = sorted(all_fingerprints.items(), key=lambda x: -x[1])[:15]

    # Load pipeline manifest for health info
    manifest = _load_manifest(config)

    return request.app.state.templates.TemplateResponse(
        request,
        name="atoms.html",
        context={
            "page_title": "Atoms Pipeline",
            "organs": organs,
            "total_tasks": total_tasks,
            "total_pending": total_pending,
            "total_prompts": total_prompts,
            "total_xlinks": total_xlinks,
            "top_fingerprints": top_fps,
            "link_matrix": link_matrix,
            "manifest": manifest,
        },
    )


@router.get("/api")
async def atoms_api(request: Request):
    """JSON endpoint for atom rollup data."""
    config = request.app.state.path_config
    rollups = load_atom_rollups(config)
    manifest = _load_manifest(config)
    return {
        "organs": len(rollups),
        "rollups": rollups,
        "manifest": manifest,
    }


def _load_manifest(config: PathConfig | None = None) -> dict:
    """Load pipeline-manifest.json if available."""
    import json
    try:
        from organvm_engine.paths import atoms_dir
        path = atoms_dir(config) / "pipeline-manifest.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}
