"""Integration tests for Phase 3 components.

Tests the complete Phase 3 workflow: context injection + plugin loading + monitoring + state persistence.
Covers:
- Context engine with domain knowledge injection
- Plugin loading and execution
- Langfuse monitoring integration
- State persistence across conversations
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

from context_engine.base import ContextEngine
from context_engine.insurance_context import InsuranceContextProvider
from context_engine.storage import InMemoryContextStorage
from plugins.plugin_loader import PluginLoader
from plugins.base import ToolPlugin
from monitoring.langfuse_integration import LangfuseMonitor


@pytest.mark.asyncio
async def test_full_workflow_with_context():
    """Test full workflow: context injection + tools + monitoring.
    
    Workflow:
    1. Initialize context engine
    2. Register insurance context provider
    3. Inject domain knowledge into prompt
    4. Verify context enrichment
    
    This tests the core Phase 3 feature: domain-aware prompt augmentation.
    """
    # Step 1: Initialize context engine
    engine = ContextEngine()
    assert engine is not None
    assert hasattr(engine, 'register_provider')
    assert hasattr(engine, 'inject_context')
    
    # Step 2: Register insurance context provider
    provider = InsuranceContextProvider()
    engine.register_provider("insurance", provider)
    
    assert "insurance" in engine.providers
    assert engine.providers["insurance"] == provider
    
    # Step 3: Test context injection with roubo (theft) sinistro
    prompt = "Analise este sinistro de roubo de moto"
    injected = await engine.inject_context(
        prompt=prompt,
        providers=["insurance"],
        context_data={
            "sinistro_tipo": "roubo",
            "veiculo_tipo": "moto"
        }
    )
    
    # Step 4: Verify context was injected
    assert injected is not None
    assert isinstance(injected, str)
    assert len(injected) > len(prompt)  # Context added
    assert "roubo" in injected.lower()
    assert "Context:" in injected
    assert "User Query:" in injected
    
    # Verify specific domain knowledge was injected
    assert "Boletim de Ocorrência" in injected or "BO" in injected or "regras" in injected.lower()
    
    # Step 5: Test with colisao (collision) sinistro
    prompt2 = "Analise este sinistro de colisao"
    injected2 = await engine.inject_context(
        prompt=prompt2,
        providers=["insurance"],
        context_data={"sinistro_tipo": "colisao"}
    )
    
    assert injected2 is not None
    assert len(injected2) > len(prompt2)
    
    # Different sinistro types should produce different context
    assert injected != injected2
    
    print("✓ Full workflow with context injection passed")


@pytest.mark.asyncio
async def test_plugin_loading_and_execution():
    """Test loading and executing plugins.
    
    Workflow:
    1. Initialize plugin loader
    2. Discover available plugins
    3. Register tool plugin
    4. Verify plugin execution capability
    
    This tests Phase 3's plugin system for dynamic tool registration.
    """
    # Step 1: Initialize plugin loader
    loader = PluginLoader(plugins_dir="plugins/enabled")
    assert loader is not None
    assert hasattr(loader, 'load_plugins')
    assert hasattr(loader, 'register_tool_plugin')
    assert hasattr(loader, 'discover_plugins')
    
    # Step 2: Discover plugins
    discovered = await loader.discover_plugins()
    assert discovered is not None
    assert isinstance(discovered, dict)
    assert "tools" in discovered
    assert "skills" in discovered
    assert "context" in discovered
    
    # Step 3: Create and register a mock tool plugin
    class MockSinistroTool(ToolPlugin):
        """Mock tool for testing plugin system."""
        name = "mock_sinistro_extractor"
        version = "1.0.0"
        tool_name = "extract_fields"
        
        async def initialize(self):
            """Initialize the plugin."""
            pass
        
        async def execute(self, **kwargs) -> Dict[str, Any]:
            """Extract fields from documento."""
            documento_tipo = kwargs.get("documento_tipo", "boletim_ocorrencia")
            documento_texto = kwargs.get("documento_texto", "")
            
            return {
                "sucesso": True,
                "documento_tipo": documento_tipo,
                "campos_extraidos": {
                    "numero_bo": "12345",
                    "data_sinistro": "2026-05-27",
                    "tipo_sinistro": "roubo"
                }
            }
    
    # Step 4: Register the plugin
    plugin = MockSinistroTool()
    loader.register_tool_plugin(plugin)
    
    assert plugin.name in loader.tool_plugins
    assert loader.tool_plugins[plugin.name] == plugin
    
    # Step 5: Execute the plugin
    result = await plugin.execute(
        documento_tipo="boletim_ocorrencia",
        documento_texto="Número BO: 12345"
    )
    
    assert result["sucesso"] is True
    assert "campos_extraidos" in result
    assert result["campos_extraidos"]["numero_bo"] == "12345"
    
    # Step 6: Verify plugin is accessible via loader
    plugins = loader.get_plugins(plugin_type="tool")
    assert plugin.name in plugins
    
    print("✓ Plugin loading and execution passed")


@pytest.mark.asyncio
async def test_monitoring_integration():
    """Test monitoring of tool execution with Langfuse.
    
    Workflow:
    1. Initialize Langfuse monitor
    2. Trace an operation execution
    3. Create spans for tracking
    4. Log operation costs
    
    This tests Phase 3's observability layer for tracking agent operations.
    """
    # Step 1: Initialize monitor without keys (graceful mode)
    monitor = LangfuseMonitor(public_key=None, secret_key=None)
    assert monitor is not None
    assert hasattr(monitor, 'trace_execution')
    assert hasattr(monitor, 'create_span')
    assert hasattr(monitor, 'log_cost')
    
    # Step 2: Trace an operation (should gracefully handle missing keys)
    await monitor.trace_execution(
        operation_name="extract_fields",
        input_data={"documento": "BO: 12345", "tipo": "boletim"},
        output_data={"numero_bo": "12345", "sucesso": True},
        metadata={"sinistro_id": "sin_001", "conversation_id": "conv_001"}
    )
    
    # No exception should be raised
    assert monitor is not None
    
    # Step 3: Create a span
    span = await monitor.create_span(
        name="extract_operation",
        input={"documento_tipo": "boletim_ocorrencia"},
        metadata={"sinistro_id": "sin_001"}
    )
    
    assert span is not None
    assert isinstance(span, dict)
    assert span["name"] == "extract_operation"
    assert "span_id" in span
    assert span["input"]["documento_tipo"] == "boletim_ocorrencia"
    
    # Step 4: Create child span (tracing hierarchy)
    child_span = await monitor.create_span(
        name="validate_fields",
        input={"campo": "numero_bo", "valor": "12345"},
        parent_span_id=span["span_id"]
    )
    
    assert child_span is not None
    assert child_span["parent_span_id"] == span["span_id"]
    
    # Step 5: Log costs
    await monitor.log_cost(
        operation="extract_fields",
        model="gpt-4",
        input_tokens=150,
        output_tokens=50,
        cost_usd=0.0045
    )
    
    # Should complete without error
    assert monitor is not None
    
    print("✓ Monitoring integration passed")


@pytest.mark.asyncio
async def test_state_persistence():
    """Test state persistence across conversations.
    
    Workflow:
    1. Initialize context storage (in-memory for Phase 3)
    2. Save conversation state
    3. Load conversation state
    4. Update state
    5. Verify persistence and retrieval
    
    This tests Phase 3's state management for maintaining sinistro processing context.
    """
    # Step 1: Initialize in-memory storage
    storage = InMemoryContextStorage()
    assert storage is not None
    assert hasattr(storage, 'save')
    assert hasattr(storage, 'load')
    assert hasattr(storage, 'delete')
    
    # Step 2: Save initial conversation state
    conversation_id = "conv_phase3_001"
    sinistro_id = "sin_phase3_001"
    
    initial_state = {
        "etapa": "triagem",
        "sinistro_tipo": "roubo",
        "veiculo_tipo": "moto",
        "score_fraude": 25,
        "campos_extraidos": {
            "numero_bo": "98765",
            "data_sinistro": "2026-05-27",
            "valor_reivindicado": 35000.00
        }
    }
    
    saved = await storage.save(
        key=f"conv_{conversation_id}",
        data=initial_state
    )
    
    assert saved is True
    
    # Step 3: Load conversation state
    loaded_state = await storage.load(key=f"conv_{conversation_id}")
    
    assert loaded_state is not None
    assert loaded_state["etapa"] == "triagem"
    assert loaded_state["sinistro_tipo"] == "roubo"
    assert loaded_state["score_fraude"] == 25
    assert loaded_state["campos_extraidos"]["numero_bo"] == "98765"
    
    # Step 4: Update state (simulate workflow progression)
    updated_state = loaded_state.copy()
    updated_state["etapa"] = "validacao"
    updated_state["score_fraude"] = 42
    
    saved_update = await storage.save(
        key=f"conv_{conversation_id}",
        data=updated_state
    )
    
    assert saved_update is True
    
    # Step 5: Verify updated state is persisted
    reloaded_state = await storage.load(key=f"conv_{conversation_id}")
    
    assert reloaded_state is not None
    assert reloaded_state["etapa"] == "validacao"
    assert reloaded_state["score_fraude"] == 42
    
    # Step 6: Delete state
    deleted = await storage.delete(key=f"conv_{conversation_id}")
    assert deleted is True
    
    # Step 7: Verify deletion
    final_state = await storage.load(key=f"conv_{conversation_id}")
    assert final_state is None
    
    print("✓ State persistence passed")


@pytest.mark.asyncio
async def test_context_caching():
    """Test context caching for performance optimization.
    
    Workflow:
    1. Create context engine
    2. Register provider
    3. Inject context with cache key
    4. Retrieve from cache on subsequent calls
    5. Verify cache hit
    
    This tests Phase 3's caching layer for reducing context injection latency.
    """
    # Step 1: Initialize context engine
    engine = ContextEngine()
    provider = InsuranceContextProvider()
    engine.register_provider("insurance", provider)
    
    # Step 2: Inject context with cache
    prompt = "Analise este sinistro"
    context_data = {"sinistro_tipo": "colisao", "veiculo_tipo": "carro"}
    
    injected = await engine.inject_context(
        prompt=prompt,
        providers=["insurance"],
        context_data=context_data
    )
    
    # Step 3: Cache the result
    cache_key = "colisao_carro_context"
    await engine.cache_context(
        cache_key=cache_key,
        context={
            "prompt": injected,
            "provider": "insurance",
            "data": context_data
        }
    )
    
    # Step 4: Retrieve from cache
    cached = await engine.get_cached_context(cache_key)
    
    assert cached is not None
    assert cached["prompt"] == injected
    assert cached["data"]["sinistro_tipo"] == "colisao"
    
    # Step 5: Verify cache is used for subsequent calls
    same_cached = await engine.get_cached_context(cache_key)
    assert same_cached == cached
    
    print("✓ Context caching passed")


@pytest.mark.asyncio
async def test_multiple_context_providers():
    """Test using multiple context providers simultaneously.
    
    Workflow:
    1. Create multiple context providers
    2. Register all providers
    3. Inject context from multiple sources
    4. Verify combined context
    
    This tests Phase 3's multi-provider context system for comprehensive knowledge injection.
    """
    # Step 1: Initialize engine
    engine = ContextEngine()
    
    # Step 2: Create primary provider
    insurance_provider = InsuranceContextProvider()
    engine.register_provider("insurance", insurance_provider)
    
    # Step 3: Create and register secondary provider
    from context_engine.base import ContextProvider
    
    class WorkflowContextProvider(ContextProvider):
        """Provides workflow-specific context."""
        async def get_context(self, **kwargs) -> Dict[str, Any]:
            return {
                "workflow_steps": [
                    "triagem", "extração", "validação",
                    "fraude_scoring", "análise_cobertura"
                ],
                "current_step": "extração",
                "sla_days": 10
            }
    
    workflow_provider = WorkflowContextProvider()
    engine.register_provider("workflow", workflow_provider)
    
    # Step 4: Inject context from both providers
    prompt = "Processar sinistro"
    injected = await engine.inject_context(
        prompt=prompt,
        providers=["insurance", "workflow"],
        context_data={"sinistro_tipo": "incendio"}
    )
    
    # Step 5: Verify both contexts are present
    assert injected is not None
    assert len(injected) > len(prompt)
    assert "incendio" in injected.lower() or "incêndio" in injected.lower()
    assert "workflow_steps" in injected
    assert "triagem" in injected
    
    print("✓ Multiple context providers passed")


@pytest.mark.asyncio
async def test_plugin_with_context_integration():
    """Test plugin execution with context injection.
    
    Workflow:
    1. Create context engine with domain knowledge
    2. Create plugin that uses context
    3. Execute plugin with enriched context
    4. Verify plugin receives context data
    
    This tests the Phase 3 integration: plugins working with context-injected prompts.
    """
    # Step 1: Initialize context engine
    engine = ContextEngine()
    provider = InsuranceContextProvider()
    engine.register_provider("insurance", provider)
    
    # Step 2: Inject context
    prompt = "Analisar sinistro"
    context_data = {"sinistro_tipo": "roubo", "veiculo_tipo": "moto"}
    
    injected_prompt = await engine.inject_context(
        prompt=prompt,
        providers=["insurance"],
        context_data=context_data
    )
    
    assert injected_prompt is not None
    
    # Step 3: Create a context-aware plugin
    class ContextAwarePlugin(ToolPlugin):
        """Plugin that works with injected context."""
        name = "context_aware_analyzer"
        version = "1.0.0"
        
        async def initialize(self):
            pass
        
        async def execute(self, **kwargs) -> Dict[str, Any]:
            prompt = kwargs.get("prompt", "")
            
            # Plugin can now see injected context
            has_context = "Context:" in prompt
            has_query = "User Query:" in prompt
            
            return {
                "sucesso": True,
                "has_context": has_context,
                "has_query": has_query,
                "prompt_length": len(prompt)
            }
    
    # Step 4: Execute plugin with context
    plugin = ContextAwarePlugin()
    result = await plugin.execute(prompt=injected_prompt)
    
    assert result["sucesso"] is True
    assert result["has_context"] is True
    assert result["has_query"] is True
    assert result["prompt_length"] > len(prompt)
    
    print("✓ Plugin with context integration passed")


@pytest.mark.asyncio
async def test_error_handling_and_graceful_degradation():
    """Test error handling and graceful degradation.
    
    Workflow:
    1. Test context engine with invalid providers
    2. Test monitoring without credentials
    3. Test storage operations with missing data
    4. Verify system recovers gracefully
    
    This tests Phase 3's resilience: operations continue even with partial failures.
    """
    # Step 1: Context engine with invalid provider
    engine = ContextEngine()
    
    prompt = "Test prompt"
    injected = await engine.inject_context(
        prompt=prompt,
        providers=["nonexistent_provider"],
        context_data={}
    )
    
    # Should return original prompt on missing provider
    assert injected == prompt
    
    # Step 2: Monitor without credentials
    monitor = LangfuseMonitor(public_key=None, secret_key=None)
    
    # Should not raise exception
    await monitor.trace_execution(
        operation_name="test",
        input_data={},
        output_data={}
    )
    
    assert monitor is not None
    
    # Step 3: Storage with missing keys
    storage = InMemoryContextStorage()
    
    loaded = await storage.load(key="nonexistent_key")
    assert loaded is None
    
    # Step 4: Delete nonexistent key
    deleted = await storage.delete(key="nonexistent_key")
    assert deleted is False
    
    print("✓ Error handling and graceful degradation passed")
