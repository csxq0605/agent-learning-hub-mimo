"""Tests for SettingsManager - 4-level hierarchy with deny-rule precedence."""

import json
import os
import pytest
from unittest.mock import patch
from mimo_harness.settings import SettingsManager, SETTINGS_LEVELS


class TestSettingsManagerHierarchy:
    """Test 4-level hierarchy merging: managed -> user -> project -> local."""

    def test_empty_settings_when_no_files(self, tmp_path):
        """Missing files at all levels should produce empty settings."""
        # Patch Path.home() to avoid reading real user settings
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("anything") is None
        assert mgr.raw == {}

    def test_single_level_managed(self, tmp_path):
        """Managed level settings are loaded correctly."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "managed.json").write_text(json.dumps({
            "model": "enterprise-model",
            "max_steps": 10,
        }))
        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("model") == "enterprise-model"
        assert mgr.get("max_steps") == 10

    def test_user_overrides_managed(self, tmp_path):
        """User level overrides managed level for non-deny keys."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        # Managed
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "managed.json").write_text(json.dumps({"model": "managed-model"}))
        # User
        user_mimo = fake_home / ".mimo"
        user_mimo.mkdir()
        (user_mimo / "settings.json").write_text(json.dumps({"model": "user-model"}))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("model") == "user-model"

    def test_project_overrides_user(self, tmp_path):
        """Project level overrides user level for non-deny keys."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        # User
        user_mimo = fake_home / ".mimo"
        user_mimo.mkdir()
        (user_mimo / "settings.json").write_text(json.dumps({"model": "user-model"}))
        # Project
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text(json.dumps({"model": "project-model"}))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("model") == "project-model"

    def test_local_overrides_project(self, tmp_path):
        """Local level overrides project level for non-deny keys."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        # Project
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text(json.dumps({"model": "project-model"}))
        # Local
        (mimo_dir / "settings.local.json").write_text(json.dumps({"model": "local-model"}))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("model") == "local-model"

    def test_full_hierarchy(self, tmp_path):
        """All 4 levels merge correctly with later levels winning."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        user_mimo = fake_home / ".mimo"
        user_mimo.mkdir()

        (mimo_dir / "managed.json").write_text(json.dumps({
            "model": "managed",
            "max_steps": 5,
            "theme": "dark",
        }))
        (user_mimo / "settings.json").write_text(json.dumps({
            "model": "user",
            "verbose": True,
        }))
        (mimo_dir / "settings.json").write_text(json.dumps({
            "model": "project",
            "max_steps": 10,
        }))
        (mimo_dir / "settings.local.json").write_text(json.dumps({
            "model": "local",
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        # local wins for model
        assert mgr.get("model") == "local"
        # project wins for max_steps (managed also had it, but project is later)
        assert mgr.get("max_steps") == 10
        # user provided verbose
        assert mgr.get("verbose") is True
        # managed provided theme (no override)
        assert mgr.get("theme") == "dark"


class TestSettingsDenyRules:
    """Test that deny rules accumulate across levels and cannot be overridden."""

    def test_deny_rules_accumulate_from_managed(self, tmp_path):
        """Deny rules from managed level are present."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "managed.json").write_text(json.dumps({
            "permissions": {"deny": ["rm -rf *"]},
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        deny = mgr.get_nested("permissions", "deny")
        assert "rm -rf *" in deny

    def test_deny_rules_accumulate_across_levels(self, tmp_path):
        """Deny rules from multiple levels are merged (union), not replaced."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        user_mimo = fake_home / ".mimo"
        user_mimo.mkdir()

        (mimo_dir / "managed.json").write_text(json.dumps({
            "permissions": {"deny": ["rm -rf *"]},
        }))
        (user_mimo / "settings.json").write_text(json.dumps({
            "permissions": {"deny": ["curl *"]},
        }))
        (mimo_dir / "settings.json").write_text(json.dumps({
            "permissions": {"deny": ["wget *"]},
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        deny = mgr.get_nested("permissions", "deny")
        assert "rm -rf *" in deny
        assert "curl *" in deny
        assert "wget *" in deny

    def test_deny_rules_not_overridden_by_later_level(self, tmp_path):
        """Later levels cannot remove deny rules from earlier levels."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()

        (mimo_dir / "managed.json").write_text(json.dumps({
            "permissions": {"deny": ["rm -rf *", "curl *"]},
        }))
        # Local tries to "override" deny with fewer rules
        (mimo_dir / "settings.local.json").write_text(json.dumps({
            "permissions": {"deny": ["curl *"]},
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        deny = mgr.get_nested("permissions", "deny")
        # Both original deny rules should still be present
        assert "rm -rf *" in deny
        assert "curl *" in deny

    def test_deny_rules_no_duplicates(self, tmp_path):
        """Duplicate deny rules across levels are deduplicated."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        user_mimo = fake_home / ".mimo"
        user_mimo.mkdir()

        (mimo_dir / "managed.json").write_text(json.dumps({
            "permissions": {"deny": ["rm -rf *"]},
        }))
        (user_mimo / "settings.json").write_text(json.dumps({
            "permissions": {"deny": ["rm -rf *"]},
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        deny = mgr.get_nested("permissions", "deny")
        assert deny.count("rm -rf *") == 1


class TestSettingsGetMethods:
    """Test get() and get_nested() methods."""

    def test_get_returns_default_for_missing(self, tmp_path):
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("nonexistent") is None
        assert mgr.get("nonexistent", "fallback") == "fallback"

    def test_get_nested_single_key(self, tmp_path):
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text(json.dumps({
            "permissions": {"allow": ["read_file"]},
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get_nested("permissions", "allow") == ["read_file"]

    def test_get_nested_missing_path(self, tmp_path):
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get_nested("permissions", "allow") is None
        assert mgr.get_nested("permissions", "allow", default=[]) == []

    def test_get_nested_non_dict_intermediate(self, tmp_path):
        """If an intermediate key is not a dict, return default."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text(json.dumps({
            "model": "test-model",
        }))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        # "model" is a string, not a dict, so nested access returns default
        assert mgr.get_nested("model", "subkey", default="nope") == "nope"

    def test_raw_returns_copy(self, tmp_path):
        """raw property returns a copy, not internal state."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text(json.dumps({"key": "value"}))

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        raw = mgr.raw
        raw["key"] = "modified"
        assert mgr.get("key") == "value"


class TestSettingsMalformedFiles:
    """Test graceful handling of malformed or missing files."""

    def test_invalid_json_handled(self, tmp_path):
        """Invalid JSON in a settings file is silently skipped."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text("{not valid json!!!")

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.raw == {}

    def test_empty_file_handled(self, tmp_path):
        """Empty settings file is silently skipped."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        (mimo_dir / "settings.json").write_text("")

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.raw == {}

    def test_partial_valid_partial_invalid(self, tmp_path):
        """Valid files are loaded even if other files are invalid."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        mimo_dir = tmp_path / ".mimo"
        mimo_dir.mkdir()
        # Managed is valid
        (mimo_dir / "managed.json").write_text(json.dumps({"model": "ok"}))
        # Project is invalid
        (mimo_dir / "settings.json").write_text("GARBAGE")

        with patch("mimo_harness.settings.Path.home", return_value=fake_home):
            mgr = SettingsManager(str(tmp_path))
        assert mgr.get("model") == "ok"


class TestSettingsLevelsConstant:
    """Test SETTINGS_LEVELS constant."""

    def test_levels_order(self):
        assert SETTINGS_LEVELS == ["managed", "user", "project", "local"]

    def test_levels_length(self):
        assert len(SETTINGS_LEVELS) == 4
