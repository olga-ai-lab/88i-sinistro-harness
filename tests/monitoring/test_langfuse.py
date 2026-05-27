"""Tests for Langfuse integration."""

import pytest
from monitoring.langfuse_integration import LangfuseMonitor
from monitoring.tracing import trace_tool_execution


@pytest.mark.asyncio
async def test_langfuse_monitor_initialization():
    """Test Langfuse monitor initialization."""
    monitor = LangfuseMonitor(
        public_key="test_key",
        secret_key="test_secret"
    )
    assert monitor is not None
    assert hasattr(monitor, 'trace_execution')


@pytest.mark.asyncio
async def test_trace_decorator():
    """Test trace decorator for tool execution."""
    
    @trace_tool_execution("test_tool")
    async def test_tool(input_data):
        return {"sucesso": True, "output": input_data}
    
    result = await test_tool({"test": "data"})
    assert result["sucesso"] is True


@pytest.mark.asyncio
async def test_span_creation():
    """Test creating spans for operations."""
    monitor = LangfuseMonitor(
        public_key="test_key",
        secret_key="test_secret"
    )
    
    span = await monitor.create_span(
        name="extract_fields",
        input={"documento": "..."},
        metadata={"sinistro_id": "sin_001"}
    )
    
    assert span is not None
