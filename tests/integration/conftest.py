"""Integration test fixtures — skip tests when backends are unavailable."""

import os

import pytest
import requests


@pytest.fixture(autouse=True)
def _require_ltzf_backend():
    """Skip integration tests if no LTZF backend is reachable."""
    api_url = os.getenv("LTZF_API_URL", "http://localhost:8080")
    try:
        resp = requests.get(f"{api_url}/health", timeout=2)
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
        pytest.skip(f"LTZF backend not reachable at {api_url}")
