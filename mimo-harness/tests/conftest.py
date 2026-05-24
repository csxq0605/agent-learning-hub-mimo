"""Pytest configuration - set env vars for testing."""

import os

# Set test environment variables before any imports
os.environ.setdefault("MIMO_API_KEY", "test-key-for-testing")
os.environ.setdefault("MIMO_BASE_URL", "http://localhost:8080/v1")
os.environ.setdefault("MIMO_MODEL", "test-model")
