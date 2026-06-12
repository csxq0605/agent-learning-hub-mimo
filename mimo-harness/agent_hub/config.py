"""Configuration loader - reads from .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path.cwd() / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


def _get(key: str, default: str = "") -> str:
    val = os.environ.get(key, default)
    return val


MIMO_BASE_URL = _get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_API_KEY = _get("MIMO_API_KEY", "")
MIMO_MODEL = _get("MIMO_MODEL", "mimo-v2.5-pro")


def require_api_key() -> str:
    """Get API key, raising if not configured. Call this at runtime, not import time."""
    if not MIMO_API_KEY:
        raise EnvironmentError(
            "Missing MIMO_API_KEY. Create a .env file with MIMO_API_KEY=... (see .env.example)"
        )
    return MIMO_API_KEY
