"""Tests for 88i LangGraph tool."""

import pytest
from tools.registry import registry


@pytest.mark.asyncio
async def test_langraph_tool_registered():
    """Verify langraph tools are registered."""
    # Import to trigger auto-registration
    import tools._88i_langraph_tool  # noqa: F401
    
    tool_names = registry.get_all_tool_names()
    assert "langraph_save_state" in tool_names
    assert "langraph_load_state" in tool_names
    assert "langraph_update_state" in tool_names


@pytest.mark.asyncio
async def test_save_state():
    """Test saving conversation state."""
    # Import to trigger auto-registration
    import tools._88i_langraph_tool  # noqa: F401
    from tools.registry import registry
    
    tool_entry = registry.get_entry("langraph_save_state")
    assert tool_entry is not None
    
    result = await tool_entry.handler({
        "conversation_id": "conv_001",
        "sinistro_id": "sin_001",
        "estado": {
            "etapa_atual": "validacao",
            "campos_extraidos": {"numero_bo": "12345"},
            "score_fraude": 25
        }
    })
    
    assert result["sucesso"] is True
    assert result["conversation_id"] == "conv_001"


@pytest.mark.asyncio
async def test_load_state():
    """Test loading conversation state."""
    # Import to trigger auto-registration
    import tools._88i_langraph_tool  # noqa: F401
    from tools.registry import registry
    
    tool_entry = registry.get_entry("langraph_load_state")
    assert tool_entry is not None
    
    result = await tool_entry.handler({
        "conversation_id": "conv_001"
    })
    
    # Initial state may be empty
    assert result["sucesso"] is True
    assert "conversation_id" in result


@pytest.mark.asyncio
async def test_update_state():
    """Test updating conversation state."""
    # Import to trigger auto-registration
    import tools._88i_langraph_tool  # noqa: F401
    from tools.registry import registry
    
    tool_entry = registry.get_entry("langraph_update_state")
    assert tool_entry is not None
    
    result = await tool_entry.handler({
        "conversation_id": "conv_001",
        "atualizacoes": {
            "etapa_atual": "fraude_scoring"
        }
    })
    
    assert result["sucesso"] is True
