"""Configuration loader — models.json is the single source of truth.

Priority:
1. models.json (providers.defaults.main → provider's base_url/api_key/model_name)
2. Environment variables (NEXGENT_BASE_URL, NEXGENT_API_KEY, NEXGENT_MODEL)
3. Hardcoded defaults
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path.cwd() / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _load_from_models_json() -> dict:
    """Try to load base_url/api_key/model from models.json."""
    for path in ["models.json", ".nexgent/models.json"]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                providers = data.get("providers", {})
                defaults = data.get("defaults", {})
                main_id = defaults.get("main", "")
                if "/" in main_id:
                    provider_name, model_name = main_id.split("/", 1)
                else:
                    provider_name, model_name = "", main_id
                provider = providers.get(provider_name, {})
                base_url = provider.get("base_url", "")
                api_key = provider.get("api_key", "")
                # Expand ${VAR} in api_key
                if api_key.startswith("${") and api_key.endswith("}"):
                    env_key = api_key[2:-1]
                    api_key = os.environ.get(env_key, "")
                if base_url and api_key and model_name:
                    return {
                        "base_url": base_url,
                        "api_key": api_key,
                        "model": model_name,
                    }
            except Exception:
                pass
    return {}


# Try models.json first, fall back to env vars
_models_cfg = _load_from_models_json()

NEXGENT_BASE_URL = _models_cfg.get("base_url") or _get("NEXGENT_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
NEXGENT_API_KEY = _models_cfg.get("api_key") or _get("NEXGENT_API_KEY", "")
NEXGENT_MODEL = _models_cfg.get("model") or _get("NEXGENT_MODEL", "mimo-v2.5-pro")

# Web search configuration
TAVILY_API_KEY = _get("TAVILY_API_KEY", "")

# Multi-model configuration (JSON path or inline JSON)
MODELS_CONFIG = _get("NEXGENT_MODELS_CONFIG", "")


def require_api_key() -> str:
    """Get API key, raising if not configured. Call this at runtime, not import time."""
    if not NEXGENT_API_KEY:
        raise EnvironmentError(
            "Missing NEXGENT_API_KEY. Configure in models.json (providers.defaults.main) "
            "or create a .env file with NEXGENT_API_KEY=... (see .env.example)"
        )
    return NEXGENT_API_KEY
