"""Tests for the /ontologia/ routes — entity browser, events, health."""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client():
    return TestClient(app)


def _make_fake_entity(uid="ent_repo_001", entity_type_val="REPOSITORY",
                      lifecycle_val="ACTIVE", created_at="2026-01-01T00:00:00Z"):
    """Build a fake entity object matching ontologia's EntityIdentity shape."""
    entity = MagicMock()
    entity.uid = uid
    entity.entity_type.value = entity_type_val
    entity.lifecycle_status.value = lifecycle_val
    entity.created_at = created_at
    entity.created_by = "bootstrap"
    entity.metadata = {}
    return entity


def _make_fake_name(display_name="organvm-engine", is_primary=True,
                    valid_from="2026-01-01T00:00:00Z"):
    """Build a fake name record."""
    name = MagicMock()
    name.display_name = display_name
    name.is_primary = is_primary
    name.valid_from = valid_from
    name.valid_to = None
    name.source = "bootstrap"
    return name


def _make_fake_event(event_type="entity.created", source="bootstrap",
                     timestamp="2026-01-01T12:00:00Z"):
    """Build a fake event record."""
    ev = MagicMock()
    ev.event_type = event_type
    ev.source = source
    ev.timestamp = timestamp
    ev.subject_entity = "ent_repo_001"
    ev.changed_property = None
    ev.previous_value = None
    ev.new_value = None
    return ev


def _make_fake_store(entity_count=5, entities=None, events=None):
    """Build a mock ontologia store."""
    store = MagicMock()
    store.entity_count = entity_count
    store.list_entities.return_value = entities or [_make_fake_entity()]
    store.current_name.return_value = _make_fake_name()
    store.events.return_value = events or [_make_fake_event()]
    store.name_history.return_value = [_make_fake_name()]
    store.get_entity.return_value = _make_fake_entity()
    return store


class TestOntologiaPage:
    def test_ontologia_page_returns_200(self, client):
        resp = client.get("/ontologia/")
        assert resp.status_code == 200

    def test_ontologia_page_contains_title(self, client):
        resp = client.get("/ontologia/")
        assert "Ontologia" in resp.text

    def test_ontologia_page_unavailable_graceful(self, client):
        """Page renders with available=False when store returns None."""
        with patch("dashboard.routes.ontologia._load_store", return_value=None):
            resp = client.get("/ontologia/")
        assert resp.status_code == 200
        assert "Ontologia" in resp.text

    def test_ontologia_page_with_store(self, client):
        """Page renders entity data when store is available."""
        store = _make_fake_store()
        with patch("dashboard.routes.ontologia._load_store", return_value=store):
            resp = client.get("/ontologia/")
        assert resp.status_code == 200
        assert "Ontologia" in resp.text


class TestOntologiaEvents:
    def test_events_page_returns_200(self, client):
        resp = client.get("/ontologia/events/")
        assert resp.status_code == 200

    def test_events_page_unavailable_graceful(self, client):
        with patch("dashboard.routes.ontologia._load_store", return_value=None):
            resp = client.get("/ontologia/events/")
        assert resp.status_code == 200
        assert "Ontologia" in resp.text

    def test_events_page_with_store(self, client):
        events = [_make_fake_event(timestamp=f"2026-01-0{i}T00:00:00Z") for i in range(1, 4)]
        store = _make_fake_store(events=events)
        with patch("dashboard.routes.ontologia._load_store", return_value=store):
            resp = client.get("/ontologia/events/")
        assert resp.status_code == 200


class TestOntologiaHealth:
    def test_health_page_returns_200(self, client):
        resp = client.get("/ontologia/health/")
        assert resp.status_code == 200

    def test_health_page_unavailable_graceful(self, client):
        with patch("dashboard.routes.ontologia._load_store", return_value=None):
            resp = client.get("/ontologia/health/")
        assert resp.status_code == 200
        assert "Ontologia" in resp.text

    def test_health_page_with_store(self, client):
        store = _make_fake_store()
        with patch("dashboard.routes.ontologia._load_store", return_value=store):
            resp = client.get("/ontologia/health/")
        assert resp.status_code == 200
