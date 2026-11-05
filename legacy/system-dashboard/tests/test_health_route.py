"""Tests for the /health/ route — primary health endpoint."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthPage:
    def test_health_page_returns_200(self, client):
        resp = client.get("/health/")
        assert resp.status_code == 200

    def test_health_page_contains_title(self, client):
        resp = client.get("/health/")
        assert "System Health" in resp.text

    def test_health_page_is_html(self, client):
        resp = client.get("/health/")
        assert resp.headers["content-type"].startswith("text/html")

    def test_health_page_with_empty_registry(self, client):
        """Page renders gracefully when registry returns empty data."""
        with patch("dashboard.routes.health.load_registry", return_value={}):
            resp = client.get("/health/")
        assert resp.status_code == 200
        assert "System Health" in resp.text

    def test_health_page_with_empty_metrics(self, client):
        """Page renders gracefully when metrics file is missing."""
        with patch("dashboard.routes.health.load_metrics", return_value={}):
            resp = client.get("/health/")
        assert resp.status_code == 200


class TestHealthAPI:
    def test_health_api_returns_200(self, client):
        resp = client.get("/health/api")
        assert resp.status_code == 200

    def test_health_api_returns_json(self, client):
        resp = client.get("/health/api")
        assert resp.headers["content-type"].startswith("application/json")

    def test_health_api_expected_keys(self, client):
        resp = client.get("/health/api")
        data = resp.json()
        assert "status" in data
        assert "organs" in data
        assert "all_operational" in data
        assert "total_repos" in data

    def test_health_api_status_values(self, client):
        """Status must be one of the known values."""
        resp = client.get("/health/api")
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")

    def test_health_api_types(self, client):
        resp = client.get("/health/api")
        data = resp.json()
        assert isinstance(data["organs"], int)
        assert isinstance(data["all_operational"], bool)
        assert isinstance(data["total_repos"], int)

    def test_health_api_with_mocked_data(self, client):
        """Verify API shape with controlled registry data."""
        fake_registry = {
            "organs": {
                "ORGAN-I": {
                    "name": "Theory",
                    "launch_status": "OPERATIONAL",
                    "repositories": [
                        {"tier": "flagship", "implementation_status": "ACTIVE"},
                    ],
                },
            }
        }
        fake_metrics = {"computed": {"total_repos": 42}}
        with (
            patch("dashboard.routes.health.load_registry", return_value=fake_registry),
            patch("dashboard.routes.health.load_metrics", return_value=fake_metrics),
        ):
            resp = client.get("/health/api")
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["organs"] == 1
        assert data["all_operational"] is True
        assert data["total_repos"] == 42
