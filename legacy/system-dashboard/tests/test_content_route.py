"""Tests for the /content/ route — content pipeline page."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestContentPage:
    def test_content_page_returns_200(self, client):
        resp = client.get("/content/")
        assert resp.status_code == 200

    def test_content_page_contains_title(self, client):
        resp = client.get("/content/")
        assert "Content Pipeline" in resp.text

    def test_content_page_is_html(self, client):
        resp = client.get("/content/")
        assert resp.headers["content-type"].startswith("text/html")

    def test_content_page_empty_data(self, client):
        """Page renders gracefully when no content posts exist."""
        with patch(
            "dashboard.routes.content.load_content_data",
            return_value={"posts": [], "cadence": {}},
        ):
            resp = client.get("/content/")
        assert resp.status_code == 200
        assert "Content Pipeline" in resp.text

    def test_content_page_with_posts(self, client):
        """Page renders posts when content data is available."""
        fake_data = {
            "posts": [
                {
                    "title": "Test Post",
                    "slug": "test-post",
                    "date": "2026-03-01",
                    "status": "published",
                    "word_count": 1200,
                    "path": "posts/test-post.md",
                    "hook": "A test post hook",
                    "distribution": {},
                },
                {
                    "title": "Draft Post",
                    "slug": "draft-post",
                    "date": "2026-03-10",
                    "status": "draft",
                    "word_count": 500,
                    "path": "posts/draft-post.md",
                    "hook": "",
                    "distribution": {},
                },
            ],
            "cadence": {
                "streak": 2,
                "last_post_date": "2026-03-10",
                "total_posts": 2,
                "published_count": 1,
                "draft_count": 1,
            },
        }
        with patch(
            "dashboard.routes.content.load_content_data",
            return_value=fake_data,
        ):
            resp = client.get("/content/")
        assert resp.status_code == 200
        assert "Content Pipeline" in resp.text
