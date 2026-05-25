"""Tests for configuration module."""

import os
import pytest
from unittest.mock import patch


class TestConfigEnvVars:
    def test_config_env_vars(self, monkeypatch):
        monkeypatch.setenv("MIMO_BASE_URL", "http://custom.api.com/v1")
        monkeypatch.setenv("MIMO_API_KEY", "my-secret-key")
        monkeypatch.setenv("MIMO_MODEL", "my-custom-model")
        # Re-import to pick up new env vars
        import importlib
        import mimo_harness.config
        importlib.reload(mimo_harness.config)
        assert mimo_harness.config.MIMO_BASE_URL == "http://custom.api.com/v1"
        assert mimo_harness.config.MIMO_API_KEY == "my-secret-key"
        assert mimo_harness.config.MIMO_MODEL == "my-custom-model"
        # Restore defaults
        importlib.reload(mimo_harness.config)

    def test_config_defaults(self):
        import mimo_harness.config
        # MIMO_MODEL has a default
        assert mimo_harness.config.MIMO_MODEL  # not empty
        # MIMO_BASE_URL has a default
        assert mimo_harness.config.MIMO_BASE_URL  # not empty


class TestRequireApiKey:
    def test_require_api_key_present(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key-123")
        import importlib
        import mimo_harness.config
        importlib.reload(mimo_harness.config)
        key = mimo_harness.config.require_api_key()
        assert key == "test-key-123"
        importlib.reload(mimo_harness.config)

    def test_require_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("MIMO_API_KEY", raising=False)
        import importlib
        import mimo_harness.config
        importlib.reload(mimo_harness.config)
        with pytest.raises(EnvironmentError, match="Missing MIMO_API_KEY"):
            mimo_harness.config.require_api_key()
        # Restore
        monkeypatch.setenv("MIMO_API_KEY", "test-key-for-testing")
        importlib.reload(mimo_harness.config)
