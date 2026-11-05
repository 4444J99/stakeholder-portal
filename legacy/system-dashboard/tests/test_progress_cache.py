"""Tests for progress route cache behavior via organism cache."""

from pathlib import Path

from organvm_engine.metrics import organism as organism_mod
from dashboard.routes import progress


_FAKE_WS = Path("/nonexistent/workspace")
_FAKE_REG_FILE = Path("/nonexistent/registry.json")
_FAKE_REGISTRY = {"organs": {}}


def test_organism_cache_hit_within_ttl(monkeypatch):
    organism_mod.clear_organism_cache()
    calls = {"count": 0}
    clock = {"value": 100.0}

    original_compute = organism_mod.compute_organism

    def tracking_compute(registry, **kwargs):
        calls["count"] += 1
        return original_compute(registry, **kwargs)

    monkeypatch.setattr(organism_mod, "compute_organism", tracking_compute)
    monkeypatch.setattr(organism_mod, "_get_registry_mtime", lambda _=None: 123.0)
    monkeypatch.setattr(organism_mod.time, "monotonic", lambda: clock["value"])

    first = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)
    clock["value"] = 110.0
    second = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)

    assert first is second
    assert calls["count"] == 1


def test_organism_cache_expires_by_ttl(monkeypatch):
    organism_mod.clear_organism_cache()
    calls = {"count": 0}
    clock = {"value": 10.0}

    original_compute = organism_mod.compute_organism

    def tracking_compute(registry, **kwargs):
        calls["count"] += 1
        return original_compute(registry, **kwargs)

    monkeypatch.setattr(organism_mod, "compute_organism", tracking_compute)
    monkeypatch.setattr(organism_mod, "_get_registry_mtime", lambda _=None: 456.0)
    monkeypatch.setattr(organism_mod.time, "monotonic", lambda: clock["value"])

    first = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)
    clock["value"] = 50.0  # >30s TTL
    second = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)

    assert first is not second
    assert calls["count"] == 2


def test_organism_cache_invalidates_on_registry_mtime_change(monkeypatch):
    organism_mod.clear_organism_cache()
    calls = {"count": 0}
    clock = {"value": 200.0}
    mtimes = [100.0, 100.0, 200.0]

    def fake_mtime(_=None):
        return mtimes.pop(0) if mtimes else 200.0

    original_compute = organism_mod.compute_organism

    def tracking_compute(registry, **kwargs):
        calls["count"] += 1
        return original_compute(registry, **kwargs)

    monkeypatch.setattr(organism_mod, "compute_organism", tracking_compute)
    monkeypatch.setattr(organism_mod, "_get_registry_mtime", fake_mtime)
    monkeypatch.setattr(organism_mod.time, "monotonic", lambda: clock["value"])

    first = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)
    second = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)
    clock["value"] = 205.0
    third = progress._get_organism(_FAKE_WS, _FAKE_REGISTRY, _FAKE_REG_FILE)

    assert first is second
    assert third is not second
    assert calls["count"] == 2
