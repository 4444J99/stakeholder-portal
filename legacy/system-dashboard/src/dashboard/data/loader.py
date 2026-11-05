"""Load system data from the corpus repo and organvm-engine."""

import json
from pathlib import Path

from organvm_engine.paths import PathConfig, resolve_path_config
from organvm_engine.registry import loader as _reg_loader
from organvm_engine.governance import rules as _gov_rules
from organvm_engine.metrics import timeseries as _ts


def load_registry(config: PathConfig | None = None) -> dict:
    """Load registry-v2.json, returning empty dict on failure."""
    cfg = resolve_path_config(config)
    try:
        return _reg_loader.load_registry(cfg.registry_path())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_governance_rules(config: PathConfig | None = None) -> dict:
    """Load governance-rules.json, returning empty dict on failure."""
    cfg = resolve_path_config(config)
    try:
        return _gov_rules.load_governance_rules(cfg.governance_rules_path())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_soak_snapshots(config: PathConfig | None = None) -> list[dict]:
    """Load all soak test snapshots sorted by date."""
    cfg = resolve_path_config(config)
    return _ts.load_snapshots(cfg.soak_dir())


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning empty dict on failure."""
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_metrics(config: PathConfig | None = None) -> dict:
    """Load system-metrics.json."""
    cfg = resolve_path_config(config)
    return _load_json(cfg.corpus_dir() / "system-metrics.json")


def load_essays(config: PathConfig | None = None) -> list[dict]:
    """List essay files from the corpus."""
    cfg = resolve_path_config(config)
    corpus_dir = cfg.corpus_dir()
    essays_dir = corpus_dir / "essays"
    if not essays_dir.is_dir():
        # Try _posts for Jekyll
        essays_dir = corpus_dir / "_posts"
    if not essays_dir.is_dir():
        return []

    essays = []
    for md in sorted(essays_dir.rglob("*.md")):
        title = md.stem.replace("-", " ").title()
        essays.append({
            "file": md.name,
            "title": title,
            "path": str(md.relative_to(corpus_dir)),
        })
    return essays


def load_atom_rollups(config: PathConfig | None = None) -> dict[str, dict]:
    """Load all per-organ atom rollup JSON files from workspace.

    Returns dict mapping organ key → rollup data.
    """
    from organvm_engine.organ_config import ORGANS

    rollups: dict[str, dict] = {}
    cfg = resolve_path_config(config)
    ws = cfg.workspace_root()
    for key, info in ORGANS.items():
        rollup_path = ws / info["dir"] / ".atoms" / "organ-rollup.json"
        if rollup_path.exists():
            try:
                with open(rollup_path) as f:
                    rollups[key] = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
    return rollups


def load_content_data(config: PathConfig | None = None) -> dict:
    """Load content posts and cadence report in one pass."""
    import dataclasses

    from organvm_engine.content.cadence import check_cadence
    from organvm_engine.content.reader import discover_posts

    cfg = resolve_path_config(config)
    content_path = cfg.content_dir()
    if not content_path.is_dir():
        return {"posts": [], "cadence": {}}

    posts = discover_posts(content_path)
    cadence = check_cadence(posts)

    return {
        "posts": [dataclasses.asdict(p) for p in posts],
        "cadence": dataclasses.asdict(cadence),
    }


def organ_summary(registry: dict) -> list[dict]:
    """Build per-organ summary for display."""
    organs = registry.get("organs", {})
    result = []
    for key, data in organs.items():
        repos = data.get("repositories", [])
        active = sum(1 for r in repos if r.get("implementation_status") != "ARCHIVED")
        flagships = sum(1 for r in repos if r.get("tier") == "flagship")
        result.append({
            "key": key,
            "name": data.get("name", key),
            "status": data.get("launch_status", "UNKNOWN"),
            "total": len(repos),
            "active": active,
            "flagships": flagships,
        })
    return result
