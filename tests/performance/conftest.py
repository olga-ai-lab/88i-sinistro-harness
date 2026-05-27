"""Performance testing fixtures and utilities."""

import pytest
import time
import asyncio
from typing import Callable, Any, Dict
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    operation: str
    duration_ms: float
    iterations: int
    avg_ms: float
    min_ms: float
    max_ms: float
    throughput: float  # ops/sec


@pytest.fixture
def benchmark_tracker():
    """Track benchmark results."""
    class BenchmarkTracker:
        def __init__(self):
            self.results: Dict[str, BenchmarkResult] = {}
        
        async def measure_async(
            self,
            operation: str,
            func: Callable,
            iterations: int = 100,
            *args,
            **kwargs
        ) -> BenchmarkResult:
            """Measure async function performance."""
            times = []
            
            for _ in range(iterations):
                start = time.perf_counter()
                try:
                    await func(*args, **kwargs)
                except Exception:
                    # Measure time even if function fails
                    pass
                elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
                times.append(elapsed)
            
            total_ms = sum(times)
            avg_ms = total_ms / iterations
            throughput = (iterations / total_ms) * 1000  # ops/sec
            
            result = BenchmarkResult(
                operation=operation,
                duration_ms=total_ms,
                iterations=iterations,
                avg_ms=avg_ms,
                min_ms=min(times),
                max_ms=max(times),
                throughput=throughput
            )
            
            self.results[operation] = result
            return result
        
        def report(self):
            """Print benchmark report."""
            print("\n" + "=" * 80)
            print("PERFORMANCE BENCHMARK REPORT")
            print("=" * 80)
            
            for op, result in self.results.items():
                print(f"\n{op}:")
                print(f"  Iterations:  {result.iterations}")
                print(f"  Total Time:  {result.duration_ms:.2f} ms")
                print(f"  Avg:         {result.avg_ms:.2f} ms")
                print(f"  Min:         {result.min_ms:.2f} ms")
                print(f"  Max:         {result.max_ms:.2f} ms")
                print(f"  Throughput:  {result.throughput:.2f} ops/sec")
    
    return BenchmarkTracker()


@pytest.fixture
def performance_targets():
    """Define performance targets for different operations."""
    return {
        "extract_fields": {"max_avg_ms": 100, "min_throughput": 10},
        "fraud_score": {"max_avg_ms": 150, "min_throughput": 6},
        "context_injection": {"max_avg_ms": 50, "min_throughput": 20},
        "plugin_load": {"max_avg_ms": 200, "min_throughput": 5},
        "state_save": {"max_avg_ms": 300, "min_throughput": 3},
        "monitoring_overhead": {"max_avg_ms": 10, "min_throughput": 100},
    }
