"""Tests for dashboard data loader."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import dashboard.data.loader as loader_mod
from organvm_engine.paths import PathConfig


class TestLoadRegistry:
    @patch.object(loader_mod, "_reg_loader")
    def test_returns_dict(self, mock_reg):
        mock_reg.load_registry.return_value = {"organs": {}}
        result = loader_mod.load_registry()
        assert result == {"organs": {}}

    @patch.object(loader_mod, "_reg_loader")
    def test_handles_file_not_found(self, mock_reg):
        mock_reg.load_registry.side_effect = FileNotFoundError
        result = loader_mod.load_registry()
        assert result == {}

    @patch.object(loader_mod, "_reg_loader")
    def test_handles_json_decode_error(self, mock_reg):
        mock_reg.load_registry.side_effect = json.JSONDecodeError("err", "", 0)
        result = loader_mod.load_registry()
        assert result == {}


class TestLoadGovernanceRules:
    @patch.object(loader_mod, "_gov_rules")
    def test_returns_dict(self, mock_gov):
        mock_gov.load_governance_rules.return_value = {"allowed_edges": []}
        result = loader_mod.load_governance_rules()
        assert result == {"allowed_edges": []}

    @patch.object(loader_mod, "_gov_rules")
    def test_handles_file_not_found(self, mock_gov):
        mock_gov.load_governance_rules.side_effect = FileNotFoundError
        result = loader_mod.load_governance_rules()
        assert result == {}

    @patch.object(loader_mod, "_gov_rules")
    def test_handles_json_decode_error(self, mock_gov):
        mock_gov.load_governance_rules.side_effect = json.JSONDecodeError("err", "", 0)
        result = loader_mod.load_governance_rules()
        assert result == {}


class TestLoadMetrics:
    def test_missing_file(self):
        config = PathConfig(corpus_root=Path("/nonexistent"))
        result = loader_mod.load_metrics(config)
        assert result == {}

    def test_with_file(self, tmp_path):
        metrics_file = tmp_path / "system-metrics.json"
        metrics_file.write_text(json.dumps({"total_repos": 100}))
        config = PathConfig(corpus_root=tmp_path)
        result = loader_mod.load_metrics(config)
        assert result == {"total_repos": 100}


class TestLoadEssays:
    def test_no_dir(self):
        config = PathConfig(corpus_root=Path("/nonexistent"))
        result = loader_mod.load_essays(config)
        assert result == []

    def test_with_essays_dir(self, tmp_path):
        essays_dir = tmp_path / "essays"
        essays_dir.mkdir()
        (essays_dir / "test-essay.md").write_text("# Test")
        (essays_dir / "another-one.md").write_text("# Another")
        config = PathConfig(corpus_root=tmp_path)
        result = loader_mod.load_essays(config)
        assert len(result) == 2
        assert any(e["file"] == "test-essay.md" for e in result)
        assert any(e["file"] == "another-one.md" for e in result)

    def test_falls_back_to_posts(self, tmp_path):
        posts_dir = tmp_path / "_posts"
        posts_dir.mkdir()
        (posts_dir / "post.md").write_text("# Post")
        config = PathConfig(corpus_root=tmp_path)
        result = loader_mod.load_essays(config)
        assert len(result) == 1
        assert result[0]["file"] == "post.md"

    def test_essay_structure(self, tmp_path):
        essays_dir = tmp_path / "essays"
        essays_dir.mkdir()
        (essays_dir / "my-great-essay.md").write_text("# Content")
        config = PathConfig(corpus_root=tmp_path)
        result = loader_mod.load_essays(config)
        essay = result[0]
        assert "file" in essay
        assert "title" in essay
        assert "path" in essay
        assert essay["file"] == "my-great-essay.md"
        assert essay["title"] == "My Great Essay"

    def test_ignores_non_md(self, tmp_path):
        essays_dir = tmp_path / "essays"
        essays_dir.mkdir()
        (essays_dir / "readme.txt").write_text("not markdown")
        (essays_dir / "real.md").write_text("# Real")
        config = PathConfig(corpus_root=tmp_path)
        result = loader_mod.load_essays(config)
        assert len(result) == 1
        assert result[0]["file"] == "real.md"


class TestOrganSummary:
    def test_structure(self):
        registry = {
            "organs": {
                "ORGAN-I": {
                    "name": "Theory",
                    "repositories": [
                        {"tier": "flagship", "implementation_status": "ACTIVE"},
                        {"tier": "standard", "implementation_status": "ARCHIVED"},
                        {"tier": "standard", "implementation_status": "ACTIVE"},
                    ],
                }
            }
        }
        result = loader_mod.organ_summary(registry)
        assert len(result) == 1
        summary = result[0]
        assert summary["key"] == "ORGAN-I"
        assert summary["name"] == "Theory"
        assert summary["total"] == 3
        assert summary["active"] == 2
        assert summary["flagships"] == 1

    def test_empty_registry(self):
        result = loader_mod.organ_summary({})
        assert result == []

    def test_empty_organs(self):
        result = loader_mod.organ_summary({"organs": {}})
        assert result == []

    def test_multiple_organs(self):
        registry = {
            "organs": {
                "ORGAN-I": {
                    "name": "Theory",
                    "repositories": [
                        {"tier": "flagship", "implementation_status": "ACTIVE"},
                    ],
                },
                "ORGAN-II": {
                    "name": "Poiesis",
                    "repositories": [
                        {"tier": "standard", "implementation_status": "ACTIVE"},
                        {"tier": "standard", "implementation_status": "ACTIVE"},
                    ],
                },
            }
        }
        result = loader_mod.organ_summary(registry)
        assert len(result) == 2
        keys = {s["key"] for s in result}
        assert keys == {"ORGAN-I", "ORGAN-II"}
