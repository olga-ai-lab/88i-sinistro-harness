"""Tests for 88i Supabase tool."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_supabase_tool_registered():
    """Verify supabase_tool is registered."""
    # Import to trigger auto-registration
    import tools._88i_supabase_tool  # noqa: F401
    from tools.registry import registry
    
    tool_names = registry.get_all_tool_names()
    assert "supabase_read_sinistro" in tool_names
    assert "supabase_update_sinistro" in tool_names
    assert "supabase_insert_sinistro" in tool_names


@patch("tools._88i_supabase_tool.get_supabase_client")
def test_read_sinistro(mock_supabase):
    """Test reading a sinistro from database."""
    # Import to trigger auto-registration
    import tools._88i_supabase_tool  # noqa: F401
    from tools.registry import registry
    
    # Create a mock response object with a .data attribute
    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": "sin_001",
            "segurado_id": "seg_001",
            "status": "triagem",
            "tipo": "roubo",
            "valor_indenizacao": 5000.00
        }
    ]
    
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
    mock_supabase.return_value = mock_client
    
    tool_entry = registry.get_entry("supabase_read_sinistro")
    
    result = asyncio.run(tool_entry.handler({
        "sinistro_id": "sin_001"
    }))
    
    assert result["sucesso"] is True
    assert result["sinistro"]["id"] == "sin_001"


@patch("tools._88i_supabase_tool.get_supabase_client")
def test_update_sinistro_status(mock_supabase):
    """Test updating sinistro status."""
    # Import to trigger auto-registration
    import tools._88i_supabase_tool  # noqa: F401
    from tools.registry import registry
    
    # Create a mock response object with a .data attribute
    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": "sin_001",
            "status": "analise_fraude"
        }
    ]
    
    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
    mock_supabase.return_value = mock_client
    
    tool_entry = registry.get_entry("supabase_update_sinistro")
    
    result = asyncio.run(tool_entry.handler({
        "sinistro_id": "sin_001",
        "status": "analise_fraude"
    }))
    
    assert result["sucesso"] is True
    assert result["novo_status"] == "analise_fraude"
