"""Pytest configuration for root-level tests."""
import sys
import importlib
import importlib.util
from pathlib import Path

import pytest
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
load_dotenv(REPO_ROOT / ".env")


def load_module(name: str, path: Path):
    """Import a module from a file path (handles hyphenated dirs)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def stage_module():
    """Factory fixture: call with (name, path) to load a stage module."""
    def _load(name: str, path: Path):
        return load_module(name, path)
    return _load
