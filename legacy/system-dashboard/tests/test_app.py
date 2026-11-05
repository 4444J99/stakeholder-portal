"""Tests for the system dashboard."""

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthRoutes:
    def test_health_page(self, client):
        resp = client.get("/health/")
        assert resp.status_code == 200
        assert "System Health" in resp.text

    def test_health_api(self, client):
        resp = client.get("/health/api")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_repos" in data
        assert "organs" in data


class TestRegistryRoutes:
    def test_registry_page(self, client):
        resp = client.get("/registry/")
        assert resp.status_code == 200
        assert "Registry Browser" in resp.text

    def test_registry_filter(self, client):
        resp = client.get("/registry/?organ=ORGAN-I")
        assert resp.status_code == 200


class TestGraphRoutes:
    def test_graph_page(self, client):
        resp = client.get("/graph/")
        assert resp.status_code == 200
        assert "Dependency Graph" in resp.text

    def test_graph_api(self, client):
        resp = client.get("/graph/api")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data


class TestSoakRoutes:
    def test_soak_page(self, client):
        resp = client.get("/soak/")
        assert resp.status_code == 200
        assert "VIGILIA" in resp.text


class TestEssayRoutes:
    def test_essays_page(self, client):
        resp = client.get("/essays/")
        assert resp.status_code == 200
        assert "Essays" in resp.text


class TestOmegaRoutes:
    def test_omega_page(self, client):
        resp = client.get("/omega/")
        assert resp.status_code == 200
        assert "Omega Scorecard" in resp.text

    def test_omega_has_criteria(self, client):
        resp = client.get("/omega/")
        assert "MET" in resp.text or "NOT MET" in resp.text


class TestAtomsRoutes:
    def test_atoms_page_loads(self, client):
        resp = client.get("/atoms/")
        assert resp.status_code == 200
        assert "Atoms Pipeline" in resp.text

    def test_atoms_api(self, client):
        resp = client.get("/atoms/api")
        assert resp.status_code == 200
        data = resp.json()
        assert "organs" in data
        assert "rollups" in data

    def test_atoms_page_no_data(self, client):
        """Graceful when no rollups exist."""
        resp = client.get("/atoms/")
        assert resp.status_code == 200
        # Should still render the page structure
        assert "Pipeline Health" in resp.text


class TestProgressRoutes:
    def test_progress_page(self, client):
        resp = client.get("/progress/")
        assert resp.status_code == 200
        assert "Progress" in resp.text

    def test_progress_api(self, client):
        resp = client.get("/progress/api")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_progress_api_gates(self, client):
        resp = client.get("/progress/api/gates")
        assert resp.status_code == 200

    def test_progress_api_blockers(self, client):
        resp = client.get("/progress/api/blockers")
        assert resp.status_code == 200

    def test_progress_repo_not_found(self, client):
        resp = client.get("/progress/repo/nonexistent-repo-xyz")
        assert resp.status_code == 404


class TestOntologiaRoutes:
    def test_ontologia_page(self, client):
        resp = client.get("/ontologia/")
        assert resp.status_code == 200
        assert "Ontologia" in resp.text

    def test_ontologia_events(self, client):
        resp = client.get("/ontologia/events/")
        assert resp.status_code == 200
        assert "Ontologia" in resp.text


class TestContentRoutes:
    def test_content_page(self, client):
        resp = client.get("/content/")
        assert resp.status_code == 200
        assert "Content Pipeline" in resp.text


class TestNetworkPage:
    def test_network_page(self, client):
        resp = client.get("/network/")
        assert resp.status_code == 200
        assert "Network Testament" in resp.text

    def test_network_api(self, client):
        resp = client.get("/network/api")
        assert resp.status_code == 200
        data = resp.json()
        assert "density" in data
        assert "coverage" in data
        assert "maps_count" in data


class TestTriviumRoutes:
    def test_trivium_page(self, client):
        resp = client.get("/trivium/")
        assert resp.status_code == 200
        assert "Dialectica Universalis" in resp.text

    def test_trivium_page_has_dialects(self, client):
        resp = client.get("/trivium/")
        assert "FORMAL_LOGIC" in resp.text or "formal_logic" in resp.text

    def test_trivium_page_has_tiers(self, client):
        resp = client.get("/trivium/")
        assert "FORMAL" in resp.text or "formal" in resp.text


class TestRootRedirect:
    def test_root_redirects(self, client):
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 307
        assert "/health/" in resp.headers["location"]
