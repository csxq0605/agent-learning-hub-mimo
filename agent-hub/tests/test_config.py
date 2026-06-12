"""Tests for configuration module."""

import os
import pytest
import importlib
import agent_hub.config


@pytest.fixture(autouse=True)
def _restore_config():
    """Reload config after each test to restore original module-level values."""
    yield
    importlib.reload(agent_hub.config)


class TestConfigEnvVars:
    def test_config_env_vars(self, monkeypatch):
        monkeypatch.setenv("MIMO_BASE_URL", "http://custom.api.com/v1")
        monkeypatch.setenv("MIMO_API_KEY", "my-secret-key")
        monkeypatch.setenv("MIMO_MODEL", "my-custom-model")
        importlib.reload(agent_hub.config)
        assert agent_hub.config.MIMO_BASE_URL == "http://custom.api.com/v1"
        assert agent_hub.config.MIMO_API_KEY == "my-secret-key"
        assert agent_hub.config.MIMO_MODEL == "my-custom-model"

    def test_config_defaults(self):
        assert agent_hub.config.MIMO_MODEL  # not empty
        assert agent_hub.config.MIMO_BASE_URL  # not empty


class TestRequireApiKey:
    def test_require_api_key_present(self, monkeypatch):
        monkeypatch.setenv("MIMO_API_KEY", "test-key-123")
        importlib.reload(agent_hub.config)
        key = agent_hub.config.require_api_key()
        assert key == "test-key-123"

    def test_require_api_key_missing(self, monkeypatch):
        monkeypatch.setattr(agent_hub.config, "MIMO_API_KEY", "")
        with pytest.raises(EnvironmentError, match="Missing MIMO_API_KEY"):
            agent_hub.config.require_api_key()


class TestConfigDefaults:
    """Test config default values."""

    def test_default_base_url(self, monkeypatch):
        monkeypatch.delenv("MIMO_BASE_URL", raising=False)
        importlib.reload(agent_hub.config)
        assert "mimo" in agent_hub.config.MIMO_BASE_URL.lower() or "api" in agent_hub.config.MIMO_BASE_URL.lower()

    def test_default_model(self, monkeypatch):
        monkeypatch.delenv("MIMO_MODEL", raising=False)
        importlib.reload(agent_hub.config)
        assert "mimo" in agent_hub.config.MIMO_MODEL.lower()

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("MIMO_MODEL", "custom-model-v1")
        importlib.reload(agent_hub.config)
        assert agent_hub.config.MIMO_MODEL == "custom-model-v1"
