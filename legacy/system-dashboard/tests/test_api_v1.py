"""Tests for the REST API v1 endpoints."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import create_app


@pytest.fixture
def app():
    """Create a fresh app instance for testing."""
    return create_app()


@pytest.fixture
def client(app):
    """Client with auth bypassed (simulates localhost)."""
    with patch("dashboard.middleware.auth._is_local", return_value=True):
        yield TestClient(app)


# ── Auth tests ──────────────────────────────────────────────────────────


class TestAuth:
    def test_local_bypass(self, app):
        """Real localhost (127.0.0.1) skips auth."""
        # _is_local checks request.client.host — TestClient uses 'testclient'
        # so we patch to simulate real localhost
        with patch("dashboard.middleware.auth._is_local", return_value=True):
            c = TestClient(app)
            resp = c.get("/api/v1/organs")
            assert resp.status_code == 200

    def test_reject_unauthenticated_remote(self, app):
        """Remote requests without auth get 401."""
        with patch("dashboard.middleware.auth._is_local", return_value=False):
            c = TestClient(app)
            resp = c.get("/api/v1/organs")
            assert resp.status_code == 401

    def test_accept_api_key(self, app):
        """Valid API key is accepted."""
        with (
            patch("dashboard.middleware.auth._is_local", return_value=False),
            patch.dict("os.environ", {"ORGANVM_API_KEY": "test-key-12345"}),
        ):
            c = TestClient(app, headers={"X-API-Key": "test-key-12345"})
            resp = c.get("/api/v1/organs")
            assert resp.status_code == 200

    def test_reject_bad_api_key(self, app):
        """Invalid API key is rejected."""
        with (
            patch("dashboard.middleware.auth._is_local", return_value=False),
            patch.dict("os.environ", {"ORGANVM_API_KEY": "real-key"}),
        ):
            c = TestClient(app, headers={"X-API-Key": "wrong-key"})
            resp = c.get("/api/v1/organs")
            assert resp.status_code == 401


# ── Endpoint tests ──────────────────────────────────────────────────────


class TestStatusEndpoint:
    def test_status_returns_json(self, client):
        resp = client.get("/api/v1/status")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestOrganismEndpoint:
    def test_organism_default(self, client):
        resp = client.get("/api/v1/organism")
        assert resp.status_code == 200

    def test_organism_with_organ(self, client):
        resp = client.get("/api/v1/organism?organ=ORGAN-I")
        assert resp.status_code == 200


class TestOmegaEndpoint:
    def test_omega(self, client):
        resp = client.get("/api/v1/omega")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestCiEndpoint:
    def test_ci(self, client):
        resp = client.get("/api/v1/ci")
        assert resp.status_code == 200


class TestDeadlinesEndpoint:
    def test_deadlines_default(self, client):
        resp = client.get("/api/v1/deadlines")
        assert resp.status_code == 200

    def test_deadlines_custom_days(self, client):
        resp = client.get("/api/v1/deadlines?days=7")
        assert resp.status_code == 200


class TestPitchEndpoint:
    def test_pitch(self, client):
        resp = client.get("/api/v1/pitch")
        assert resp.status_code == 200


class TestRegistryEndpoint:
    def test_registry_all(self, client):
        resp = client.get("/api/v1/registry")
        assert resp.status_code == 200
        data = resp.json()
        assert "repos" in data

    def test_registry_filter_organ(self, client):
        resp = client.get("/api/v1/registry?organ=ORGAN-I")
        assert resp.status_code == 200

    def test_registry_name_pattern(self, client):
        resp = client.get("/api/v1/registry?name_pattern=engine")
        assert resp.status_code == 200

    def test_registry_single_repo(self, client):
        resp = client.get("/api/v1/registry/meta-organvm/organvm-engine")
        assert resp.status_code == 200


class TestOrgansEndpoint:
    def test_organs(self, client):
        resp = client.get("/api/v1/organs")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestSeedsEndpoint:
    def test_seed_repo(self, client):
        resp = client.get("/api/v1/seeds/meta-organvm/organvm-engine")
        assert resp.status_code == 200


class TestEdgesEndpoint:
    def test_edges_default(self, client):
        resp = client.get("/api/v1/edges")
        assert resp.status_code == 200

    def test_edges_with_repo(self, client):
        resp = client.get("/api/v1/edges?repo=organvm-engine")
        assert resp.status_code == 200


class TestGraphEndpoint:
    def test_graph(self, client):
        resp = client.get("/api/v1/graph")
        assert resp.status_code == 200

    def test_graph_trace(self, client):
        resp = client.get("/api/v1/graph/trace?repo=organvm-engine")
        assert resp.status_code == 200


class TestGovernanceEndpoint:
    def test_governance_audit(self, client):
        resp = client.get("/api/v1/governance/audit")
        assert resp.status_code == 200

    def test_governance_impact(self, client):
        resp = client.get("/api/v1/governance/impact/organvm-engine")
        assert resp.status_code == 200


class TestMetricsEndpoint:
    def test_metrics(self, client):
        resp = client.get("/api/v1/metrics")
        assert resp.status_code == 200


class TestEcosystemEndpoint:
    def test_ecosystem_profile(self, client):
        resp = client.get("/api/v1/ecosystem/organvm-engine")
        assert resp.status_code == 200


class TestCoordinationEndpoint:
    def test_work_board(self, client):
        resp = client.get("/api/v1/coordination/board")
        assert resp.status_code == 200


# ── Plain-text content negotiation ─────────────────────────────────────


class TestPlainTextNegotiation:
    """Verify Accept: text/plain triggers plain-text responses."""

    def test_default_returns_json(self, client):
        resp = client.get("/api/v1/status")
        assert resp.headers["content-type"].startswith("application/json")

    def test_accept_text_plain_returns_plaintext(self, client):
        resp = client.get("/api/v1/status", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/plain")
        assert "ORGANVM STATUS" in resp.text

    def test_plaintext_omega(self, client):
        resp = client.get("/api/v1/omega", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        assert "OMEGA SCORECARD" in resp.text

    def test_plaintext_registry(self, client):
        resp = client.get("/api/v1/registry", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        assert "REGISTRY" in resp.text

    def test_plaintext_governance_audit(self, client):
        resp = client.get(
            "/api/v1/governance/audit", headers={"Accept": "text/plain"},
        )
        assert resp.status_code == 200
        assert "GOVERNANCE AUDIT" in resp.text

    def test_plaintext_ci(self, client):
        resp = client.get("/api/v1/ci", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        assert "CI HEALTH" in resp.text

    def test_plaintext_deadlines(self, client):
        resp = client.get("/api/v1/deadlines", headers={"Accept": "text/plain"})
        assert resp.status_code == 200
        assert "DEADLINES" in resp.text

    def test_plaintext_coordination_board(self, client):
        resp = client.get(
            "/api/v1/coordination/board", headers={"Accept": "text/plain"},
        )
        assert resp.status_code == 200
        assert "COORDINATION BOARD" in resp.text
