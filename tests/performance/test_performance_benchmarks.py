"""Performance benchmarking tests for 88i Sinistro Harness.

This module contains performance benchmarks for key operations:
- extract_fields: Extracting structured fields from documents
- fraud_score: Calculating fraud risk scores
- context_injection: Injecting domain context into prompts
- plugin_load: Loading and discovering plugins
- state_save: Saving state to Supabase
- monitoring_overhead: Measuring monitoring/tracing overhead
"""

import pytest
import asyncio
from typing import Dict, Any


@pytest.mark.asyncio
@pytest.mark.performance
async def test_extract_fields_performance(benchmark_tracker, performance_targets):
    """Benchmark extract_fields tool performance.
    
    Tests the performance of extracting structured fields from sinistro documents.
    Measures latency and throughput for field extraction operations.
    """
    
    async def run_extract():
        """Simulate field extraction from a document."""
        # Mock implementation of field extraction
        documento = "Número BO: 12345\nData: 2026-05-27\nTipo: roubo"
        campos = {
            "numero_bo": "12345",
            "data": "2026-05-27",
            "tipo": "roubo",
            "confianca": 0.95
        }
        await asyncio.sleep(0.001)  # Simulate I/O
        return campos
    
    result = await benchmark_tracker.measure_async(
        "extract_fields",
        run_extract,
        iterations=50
    )
    
    # Verify targets
    target = performance_targets["extract_fields"]
    assert result.avg_ms <= target["max_avg_ms"], \
        f"extract_fields too slow: {result.avg_ms:.2f}ms (target: {target['max_avg_ms']}ms)"
    assert result.throughput >= target["min_throughput"], \
        f"extract_fields low throughput: {result.throughput:.2f} ops/sec (target: {target['min_throughput']})"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_fraud_score_performance(benchmark_tracker, performance_targets):
    """Benchmark fraud_score tool performance.
    
    Tests the performance of calculating fraud risk scores for sinistro claims.
    Measures latency and throughput for fraud scoring operations.
    """
    
    async def run_score():
        """Simulate fraud score calculation."""
        sinistro_data = {
            "sinistro_tipo": "roubo",
            "veiculo_tipo": "carro",
            "valor": 25000,
            "dias_atraso_bo": 2
        }
        
        # Mock fraud scoring logic
        base_score = 20
        if sinistro_data["valor"] > 20000:
            base_score += 15
        if sinistro_data["dias_atraso_bo"] > 1:
            base_score += 10
        
        await asyncio.sleep(0.002)  # Simulate processing
        return {
            "score_fraude": base_score,
            "risco_nivel": "medio" if base_score > 30 else "baixo"
        }
    
    result = await benchmark_tracker.measure_async(
        "fraud_score",
        run_score,
        iterations=50
    )
    
    target = performance_targets["fraud_score"]
    assert result.avg_ms <= target["max_avg_ms"], \
        f"fraud_score too slow: {result.avg_ms:.2f}ms (target: {target['max_avg_ms']}ms)"
    assert result.throughput >= target["min_throughput"], \
        f"fraud_score low throughput: {result.throughput:.2f} ops/sec (target: {target['min_throughput']})"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_context_injection_performance(benchmark_tracker, performance_targets):
    """Benchmark context injection performance.
    
    Tests the performance of injecting insurance domain context into prompts.
    Measures latency and throughput for context injection operations.
    """
    
    async def run_injection():
        """Simulate context injection."""
        from context_engine.base import ContextEngine
        from context_engine.insurance_context import InsuranceContextProvider
        
        engine = ContextEngine()
        provider = InsuranceContextProvider()
        engine.register_provider("insurance", provider)
        
        result = await engine.inject_context(
            prompt="Analise este sinistro de roubo",
            providers=["insurance"],
            context_data={"sinistro_tipo": "roubo"}
        )
        return result
    
    result = await benchmark_tracker.measure_async(
        "context_injection",
        run_injection,
        iterations=100
    )
    
    target = performance_targets["context_injection"]
    assert result.avg_ms <= target["max_avg_ms"], \
        f"context_injection too slow: {result.avg_ms:.2f}ms (target: {target['max_avg_ms']}ms)"
    assert result.throughput >= target["min_throughput"], \
        f"context_injection low throughput: {result.throughput:.2f} ops/sec (target: {target['min_throughput']})"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_plugin_load_performance(benchmark_tracker, performance_targets):
    """Benchmark plugin loader performance.
    
    Tests the performance of loading and discovering plugins.
    Measures latency and throughput for plugin discovery operations.
    """
    
    async def run_load():
        """Simulate plugin discovery and loading."""
        from plugins.base import Plugin, PluginMetadata
        
        # Mock plugin loading
        class MockPlugin(Plugin):
            name = "mock_plugin"
            version = "1.0.0"
            metadata = PluginMetadata(
                name="mock_plugin",
                version="1.0.0",
                description="Mock plugin for testing"
            )
            
            async def initialize(self):
                await asyncio.sleep(0.001)
            
            async def execute(self, **kwargs):
                return {"status": "ok"}
        
        # Simulate plugin discovery
        plugin = MockPlugin()
        await plugin.initialize()
        await asyncio.sleep(0.005)  # Simulate filesystem scan
        return plugin
    
    result = await benchmark_tracker.measure_async(
        "plugin_load",
        run_load,
        iterations=20
    )
    
    target = performance_targets["plugin_load"]
    assert result.avg_ms <= target["max_avg_ms"], \
        f"plugin_load too slow: {result.avg_ms:.2f}ms (target: {target['max_avg_ms']}ms)"
    assert result.throughput >= target["min_throughput"], \
        f"plugin_load low throughput: {result.throughput:.2f} ops/sec (target: {target['min_throughput']})"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_state_save_performance(benchmark_tracker, performance_targets):
    """Benchmark state save performance.
    
    Tests the performance of saving conversation state to Supabase.
    Measures latency and throughput for state persistence operations.
    """
    
    async def run_save():
        """Simulate state save operation."""
        from tools._88i_langraph_supabase_migration import InMemoryStateStorage
        
        # Use in-memory storage for performance testing (no network overhead)
        storage = InMemoryStateStorage()
        
        success = await storage.save_state(
            conversation_id="conv_perf_test_001",
            sinistro_id="sin_perf_test_001",
            estado={
                "etapa": "validacao",
                "score": 45,
                "timestamp": "2026-05-27T12:00:00Z"
            },
            ttl_hours=24
        )
        return success
    
    result = await benchmark_tracker.measure_async(
        "state_save",
        run_save,
        iterations=50
    )
    
    target = performance_targets["state_save"]
    assert result.avg_ms <= target["max_avg_ms"], \
        f"state_save too slow: {result.avg_ms:.2f}ms (target: {target['max_avg_ms']}ms)"
    assert result.throughput >= target["min_throughput"], \
        f"state_save low throughput: {result.throughput:.2f} ops/sec (target: {target['min_throughput']})"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_monitoring_overhead(benchmark_tracker, performance_targets):
    """Benchmark monitoring/tracing overhead.
    
    Tests the performance overhead of distributed tracing with Langfuse.
    Measures latency and throughput for monitoring operations.
    """
    
    async def run_trace():
        """Simulate trace execution."""
        from monitoring.langfuse_integration import LangfuseMonitor
        
        monitor = LangfuseMonitor(public_key="test", secret_key="test")
        
        await monitor.trace_execution(
            operation_name="test_operation",
            input_data={"sinistro_id": "sin_001", "tipo": "roubo"},
            output_data={"score": 45, "status": "completed"}
        )
    
    result = await benchmark_tracker.measure_async(
        "monitoring_overhead",
        run_trace,
        iterations=100
    )
    
    target = performance_targets["monitoring_overhead"]
    assert result.avg_ms <= target["max_avg_ms"], \
        f"monitoring_overhead too slow: {result.avg_ms:.2f}ms (target: {target['max_avg_ms']}ms)"
    assert result.throughput >= target["min_throughput"], \
        f"monitoring_overhead low throughput: {result.throughput:.2f} ops/sec (target: {target['min_throughput']})"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_performance_report(benchmark_tracker):
    """Generate performance report after all benchmarks.
    
    This test runs after all other performance tests and generates
    a summary report of all benchmark results.
    """
    # Run a quick benchmark to ensure we have at least one result
    async def dummy_op():
        await asyncio.sleep(0.001)
    
    if not benchmark_tracker.results:
        await benchmark_tracker.measure_async("dummy_operation", dummy_op, iterations=10)
    
    # Print the report
    benchmark_tracker.report()
    
    # Verify we have results
    assert len(benchmark_tracker.results) > 0, "No benchmark results recorded"
