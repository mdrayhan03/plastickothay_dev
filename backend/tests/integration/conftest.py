"""Integration-test fixtures."""

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Throttle counters live in the cache and would otherwise leak between tests — one test's
    submissions would exhaust another's rate limit. Dedicated throttle tests clear and drive
    the limit explicitly."""
    cache.clear()
    yield
    cache.clear()
