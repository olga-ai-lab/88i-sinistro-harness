"""Tests for 88i sinistro tools wrapper."""

import pytest
from tools.registry import registry
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_sinistro_tools_registered():
    """Verify sinistro_tools is registered in the tool registry."""
    # Import to trigger auto-registration
    import tools._88i_sinistro_tools  # noqa: F401
    
    tool_names = registry.get_all_tool_names()
    assert "sinistro_extract_fields" in tool_names
    assert "sinistro_fraud_score" in tool_names


@pytest.mark.asyncio
async def test_extract_fields_tool():
    """Test extract_fields tool invocation with mock data."""
    # Import to trigger auto-registration
    import tools._88i_sinistro_tools  # noqa: F401
    from tools.registry import registry
    
    tool_entry = registry.get_entry("sinistro_extract_fields")
    assert tool_entry is not None
    
    # Mock the skill execution
    result = await tool_entry.handler({
        "documento_tipo": "boletim_ocorrencia",
        "documento_texto": "Número BO: 12345\nData: 2026-05-27\nTipo: Roubo",
        "sinistro_id": "sin_test_001"
    })
    
    assert result["sucesso"] is True
    assert "campos_extraidos" in result
    assert result["sinistro_id"] == "sin_test_001"


@pytest.mark.asyncio
async def test_fraud_score_tool():
    """Test fraud_score tool with mock data."""
    # Import to trigger auto-registration
    import tools._88i_sinistro_tools  # noqa: F401
    from tools.registry import registry
    
    tool_entry = registry.get_entry("sinistro_fraud_score")
    assert tool_entry is not None
    
    result = await tool_entry.handler({
        "sinistro_id": "sin_test_001",
        "segurado_id": "seg_001",
        "campos_extraidos": {
            "numero_bo": "12345",
            "valor_indenizacao": 5000.00,
            "tipo_sinistro": "roubo"
        }
    })
    
    assert result["sucesso"] is True
    assert "score_fraude" in result
    assert 0 <= result["score_fraude"] <= 100
