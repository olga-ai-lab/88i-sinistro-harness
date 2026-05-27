"""Tests for 88i inngest tool."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Import the tool module to trigger registration
import tools._88i_inngest_tool


def test_inngest_tool_registered():
    """Verify inngest tools are registered."""
    from tools.registry import registry
    
    tool_names = registry.get_all_tool_names()
    assert "inngest_trigger_workflow" in tool_names
    assert "inngest_schedule_job" in tool_names


@patch("tools._88i_inngest_tool.get_inngest_client")
def test_trigger_workflow(mock_inngest):
    """Test triggering an async workflow."""
    from tools.registry import registry
    
    mock_client = AsyncMock()
    mock_client.send.return_value = {"id": "event_123"}
    mock_inngest.return_value = mock_client
    
    tool_entry = registry.get_entry("inngest_trigger_workflow")
    
    result = asyncio.run(tool_entry.handler({
        "workflow": "process_sinistro",
        "sinistro_id": "sin_001",
        "etapa": "validacao"
    }))
    
    assert result["sucesso"] is True
    assert "event_id" in result


@patch("tools._88i_inngest_tool.get_inngest_client")
def test_schedule_job(mock_inngest):
    """Test scheduling a cron job."""
    from tools.registry import registry
    
    mock_client = AsyncMock()
    mock_client.send.return_value = {"id": "cron_123"}
    mock_inngest.return_value = mock_client
    
    tool_entry = registry.get_entry("inngest_schedule_job")
    
    result = asyncio.run(tool_entry.handler({
        "job_name": "cleanup_pending",
        "schedule": "0 2 * * *",  # Daily at 2am
        "payload": {}
    }))
    
    assert result["sucesso"] is True
