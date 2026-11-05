"""Tests for the /pulse/ route."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_fake_pulse_data():
    """Build a realistic fake pulse data dict for testing."""
    from organvm_engine.pulse.affective import MoodFactors, MoodReading, SystemMood
    from organvm_engine.pulse.density import DensityProfile
    from organvm_engine.pulse.events import Event
    from organvm_engine.pulse.nerve import NerveBundle, Subscription

    mood = MoodReading(
        mood=SystemMood.STEADY,
        factors=MoodFactors(health_pct=55, density_score=42.0),
        reasoning=["No significant positive or negative signals"],
    )

    density = DensityProfile(
        declared_edges=120,
        possible_edges=10000,
        edge_saturation=0.012,
        unresolved_edges=3,
        total_repos=100,
        repos_with_seeds=80,
        repos_with_ci=40,
        repos_with_tests=35,
        repos_with_docs=60,
        repos_with_ecosystem=25,
        cross_organ_edges=15,
        organs_with_outbound=4,
        organs_with_inbound=5,
        interconnection_score=42.0,
    )

    events = [
        Event(
            event_type="registry.updated",
            source="cli",
            timestamp="2026-03-13T12:00:00+00:00",
        ),
        Event(
            event_type="mood.shifted",
            source="pulse",
            timestamp="2026-03-13T11:30:00+00:00",
        ),
    ]

    bundle = NerveBundle()
    bundle.add(Subscription(
        subscriber="meta-organvm/system-dashboard",
        event_type="registry.updated",
        source="",
        action="rebuild",
    ))
    bundle.add(Subscription(
        subscriber="organvm-vii-kerygma/kerygma-profiles",
        event_type="product.release",
        source="organvm-iii-ergon/*",
        action="notify",
    ))

    return {
        "mood": mood,
        "density": density,
        "events": events,
        "event_counts": {"registry.updated": 5, "mood.shifted": 2},
        "nerve": bundle,
        "cross_organ_edges": 15,
        "outbound_orgs": ["organvm-i-theoria", "organvm-iii-ergon"],
        "inbound_orgs": ["organvm-vii-kerygma", "meta-organvm"],
        "total_edges": 120,
        "total_nodes": 80,
        "organism_sys_pct": 55,
        "organism_total_repos": 100,
    }


class TestPulsePageWithData:
    """Test pulse page with mocked data."""

    def test_pulse_page_returns_200(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert resp.status_code == 200

    def test_pulse_page_contains_title(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "System Pulse" in resp.text

    def test_pulse_page_shows_mood(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "steady" in resp.text.lower()
        assert "Mood" in resp.text

    def test_pulse_page_shows_density(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "Density" in resp.text
        assert "42" in resp.text  # interconnection_score

    def test_pulse_page_shows_events(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "registry.updated" in resp.text
        assert "Recent Events" in resp.text

    def test_pulse_page_shows_nerve_wiring(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "Nerve Wiring" in resp.text
        assert "product.release" in resp.text

    def test_pulse_page_shows_cross_organ(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "Cross-Organ" in resp.text

    def test_pulse_page_shows_coverage_bars(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/")
        assert "Seeds" in resp.text
        assert "Coverage" in resp.text


class TestPulseAPI:
    """Test /pulse/api JSON endpoint."""

    def test_pulse_api_returns_200(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/api")
        assert resp.status_code == 200

    def test_pulse_api_returns_json_with_expected_keys(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/api")
        data = resp.json()
        assert "mood" in data
        assert "density" in data
        assert "events" in data
        assert "cross_organ_edges" in data
        assert "nerve_total" in data

    def test_pulse_api_mood_shape(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/api")
        mood = resp.json()["mood"]
        assert mood["mood"] == "steady"
        assert "glyph" in mood
        assert "reasoning" in mood

    def test_pulse_api_density_shape(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/api")
        density = resp.json()["density"]
        assert density["interconnection_score"] == 42.0
        assert density["declared_edges"] == 120

    def test_pulse_api_events_list(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            return_value=_make_fake_pulse_data(),
        ):
            resp = client.get("/pulse/api")
        events = resp.json()["events"]
        assert len(events) == 2
        assert events[0]["event_type"] == "registry.updated"


class TestPulseFallback:
    """Test graceful fallback when pulse module is unavailable."""

    def test_pulse_page_fallback_returns_200(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            side_effect=ImportError("pulse not installed"),
        ):
            resp = client.get("/pulse/")
        assert resp.status_code == 200

    def test_pulse_page_fallback_shows_error(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            side_effect=Exception("something broke"),
        ):
            resp = client.get("/pulse/")
        assert resp.status_code == 200
        assert "Pulse Unavailable" in resp.text

    def test_pulse_api_fallback_returns_error(self, client):
        with patch(
            "dashboard.routes.pulse._load_pulse_data",
            side_effect=RuntimeError("engine not available"),
        ):
            resp = client.get("/pulse/api")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data
