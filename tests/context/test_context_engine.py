"""Tests for context engine."""

import pytest
from context_engine.base import ContextEngine
from context_engine.insurance_context import InsuranceContextProvider
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_context_engine_initialization():
    """Test context engine can be initialized."""
    engine = ContextEngine()
    assert engine is not None
    assert hasattr(engine, 'register_provider')
    assert hasattr(engine, 'inject_context')


@pytest.mark.asyncio
async def test_insurance_context_provider():
    """Test insurance domain context provider."""
    provider = InsuranceContextProvider()
    context = await provider.get_context(
        sinistro_tipo="roubo",
        veiculo_tipo="moto"
    )
    
    assert context is not None
    assert "sinistro_info" in context
    assert "regras" in context["sinistro_info"]


@pytest.mark.asyncio
async def test_context_injection():
    """Test injecting context into prompt."""
    engine = ContextEngine()
    provider = InsuranceContextProvider()
    engine.register_provider("insurance", provider)
    
    prompt = "Analise este sinistro"
    injected = await engine.inject_context(
        prompt=prompt,
        providers=["insurance"],
        context_data={"sinistro_tipo": "roubo"}
    )
    
    assert injected is not None
    assert len(injected) > len(prompt)  # Context added
    assert "roubo" in injected.lower()
