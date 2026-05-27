"""Fixtures for pre-launch test suite.

Provides shared fixtures for health check, SLA compliance, and
security validation tests.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    
    yield loop
    
    try:
        loop.close()
    except RuntimeError:
        pass


@pytest.fixture
async def app_client() -> AsyncGenerator:
    """Create async test client for the FastAPI application.
    
    This fixture provides an AsyncClient that can be used to make
    HTTP requests to the application during testing.
    """
    from main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sla_targets() -> dict:
    """Provide SLA targets for validation tests.
    
    Returns:
        dict: Contains P95 latency targets in milliseconds.
    """
    return {
        "extract_p95_ms": 100,        # Extract operation P95 < 100ms
        "fraud_p95_ms": 150,          # Fraud detection P95 < 150ms
        "health_p95_ms": 50,          # Health check P95 < 50ms
        "general_p99_ms": 300,        # General operations P99 < 300ms
    }


@pytest.fixture
def required_security_headers() -> list:
    """Provide list of required security headers.
    
    Returns:
        list: HTTP header names that must be present.
    """
    return [
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Strict-Transport-Security",
        "Content-Security-Policy",
    ]


@pytest.fixture
def forbidden_headers() -> list:
    """Provide list of headers that should NOT be present.
    
    Returns:
        list: HTTP header names that must NOT be present.
    """
    return [
        "Server",
        "X-Powered-By",
        "X-AspNet-Version",
        "X-Runtime",
    ]


@pytest.fixture
def health_endpoints() -> list:
    """Provide list of health check endpoints to test.
    
    Returns:
        list: Health endpoint paths.
    """
    return [
        "/health",
        "/health/live",
        "/health/ready",
        "/health/detailed",
    ]


@pytest.fixture
def rate_limit_config() -> dict:
    """Provide rate limiting configuration.
    
    Returns:
        dict: Rate limit configuration (requests per window).
    """
    return {
        "requests_per_minute": 60,
        "test_request_count": 65,  # Slightly over limit to trigger rate limiting
    }


@pytest.fixture(scope="session")
def test_credentials() -> dict:
    """Provide test credentials and API keys.
    
    Note: These are mock credentials for testing only.
    
    Returns:
        dict: Test credentials.
    """
    return {
        "test_api_key": "test-api-key-12345",
        "test_user_id": "TEST-001",
        "test_session_id": "session-test-001",
    }


@pytest.mark.asyncio
@pytest.fixture
def mock_encryption():
    """Provide mock encryption manager.
    
    Yields an object with encrypt/decrypt methods.
    """
    class MockEncryptionManager:
        def encrypt(self, data: str) -> str:
            """Mock encryption."""
            return f"encrypted_{data}"
        
        def decrypt(self, data: str) -> str:
            """Mock decryption."""
            if data.startswith("encrypted_"):
                return data[10:]  # Remove "encrypted_" prefix
            return data
    
    yield MockEncryptionManager()
