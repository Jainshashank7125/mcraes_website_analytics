"""Pytest configuration and shared fixtures."""
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as end-to-end (requires DB and optional auth override)")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
