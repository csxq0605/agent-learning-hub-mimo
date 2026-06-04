"""Pytest configuration for root-level tests."""
import sys
import importlib
import importlib.util
import functools
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


# Import shared E2E retry logic from mimo-harness tests
_e2e_utils_path = REPO_ROOT / "mimo-harness" / "tests" / "e2e_utils.py"
_e2e_utils = load_module("e2e_utils", _e2e_utils_path)
E2E_MAX_RETRIES = _e2e_utils.E2E_MAX_RETRIES
_is_retryable = _e2e_utils._is_retryable


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    """Retry flaky E2E tests up to E2E_MAX_RETRIES times on network errors."""
    # Only retry E2E tests (in test_e2e.py)
    is_e2e = "test_e2e" in str(item.fspath)

    if not is_e2e:
        # Non-E2E tests: run normally
        yield
        return

    # E2E tests: retry only on retryable (network/API) failures
    last_exc = None
    for attempt in range(E2E_MAX_RETRIES):
        try:
            outcome = yield
            # If we get here without exception, test passed
            return
        except Exception as e:
            last_exc = e
            if not _is_retryable(e):
                # Non-retryable error (e.g. AssertionError) — fail immediately
                raise
            if attempt < E2E_MAX_RETRIES - 1:
                print(f"\n  [RETRY] {item.nodeid} failed (attempt {attempt + 1}/{E2E_MAX_RETRIES}), retrying...")
                continue
            else:
                raise last_exc
