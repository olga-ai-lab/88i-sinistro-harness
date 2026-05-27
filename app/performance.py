"""Performance optimization and SLA validation module.

Provides latency tracking, percentile calculation, and SLA compliance reporting.
"""

from __future__ import annotations

import time
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Dict, List, Optional
from collections import defaultdict
from statistics import mean, quantiles

logger = logging.getLogger(__name__)

# Target latencies (ms) for different operation types
TARGET_LATENCIES = {
    "extract": 100,
    "fraud": 150,
    "context": 50,
    "plugin": 200,
    "state": 300,
    "monitoring": 10,
}


class PerformanceOptimizer:
    """Tracks operation latencies and validates SLA compliance."""

    def __init__(self, target_latencies: Optional[Dict[str, int]] = None):
        """Initialize PerformanceOptimizer.

        Args:
            target_latencies: Dict mapping operation names to target latency (ms).
                            Defaults to TARGET_LATENCIES.
        """
        self.target_latencies = target_latencies or TARGET_LATENCIES
        self.operations: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def track_operation(
        self, operation_name: str
    ) -> Callable:
        """Decorator to track operation latency (async and sync).

        Args:
            operation_name: Name of the operation to track.

        Returns:
            Decorator function.
        """
        def decorator(func: Callable) -> Callable:
            # Check if function is async
            if asyncio.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs) -> Any:
                    start = time.perf_counter()
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        elapsed_ms = (time.perf_counter() - start) * 1000
                        self.operations[operation_name].append(elapsed_ms)
                        logger.debug(
                            f"Operation '{operation_name}' took {elapsed_ms:.2f}ms"
                        )
                return async_wrapper
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs) -> Any:
                    start = time.perf_counter()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        elapsed_ms = (time.perf_counter() - start) * 1000
                        self.operations[operation_name].append(elapsed_ms)
                        logger.debug(
                            f"Operation '{operation_name}' took {elapsed_ms:.2f}ms"
                        )
                return sync_wrapper

        return decorator

    def get_percentile(
        self, operation_name: str, percentile: float
    ) -> Optional[float]:
        """Get percentile latency for an operation.

        Args:
            operation_name: Name of the operation.
            percentile: Percentile to calculate (0-100). Supported: 50, 95, 99.

        Returns:
            Percentile latency in ms, or None if no data.
        """
        if operation_name not in self.operations:
            return None

        latencies = sorted(self.operations[operation_name])
        if not latencies:
            return None

        # For small samples, use linear interpolation
        if len(latencies) == 1:
            return latencies[0]

        # Calculate percentile using nearest-rank method
        index = int((percentile / 100) * len(latencies))
        index = min(index, len(latencies) - 1)
        return latencies[index]

    def get_report(self, operation_name: str) -> Dict[str, Any]:
        """Get comprehensive performance report for an operation.

        Returns dict with:
          - count: number of operations recorded
          - min: minimum latency (ms)
          - max: maximum latency (ms)
          - mean: mean latency (ms)
          - p50: 50th percentile latency (ms)
          - p95: 95th percentile latency (ms)
          - p99: 99th percentile latency (ms)
          - target: target latency (ms)
          - sla_breaches: count of operations exceeding target
          - compliance_pct: percentage of operations meeting SLA (0-100)

        Args:
            operation_name: Name of the operation.

        Returns:
            Dict with performance metrics.
        """
        if operation_name not in self.operations:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "p50": None,
                "p95": None,
                "p99": None,
                "target": self.target_latencies.get(operation_name),
                "sla_breaches": 0,
                "compliance_pct": 0.0,
            }

        latencies = self.operations[operation_name]
        if not latencies:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "mean": None,
                "p50": None,
                "p95": None,
                "p99": None,
                "target": self.target_latencies.get(operation_name),
                "sla_breaches": 0,
                "compliance_pct": 0.0,
            }

        target = self.target_latencies.get(operation_name)
        breaches = sum(1 for l in latencies if target and l > target)
        compliance = 0.0
        if target:
            compliance = ((len(latencies) - breaches) / len(latencies)) * 100

        return {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "mean": mean(latencies),
            "p50": self.get_percentile(operation_name, 50),
            "p95": self.get_percentile(operation_name, 95),
            "p99": self.get_percentile(operation_name, 99),
            "target": target,
            "sla_breaches": breaches,
            "compliance_pct": compliance,
        }

    def get_all_reports(self) -> Dict[str, Dict[str, Any]]:
        """Get performance reports for all tracked operations.

        Returns:
            Dict mapping operation names to their reports.
        """
        return {
            op_name: self.get_report(op_name)
            for op_name in self.operations.keys()
        }

    def reset(self, operation_name: Optional[str] = None) -> None:
        """Reset operation tracking data.

        Args:
            operation_name: If specified, reset only this operation. Otherwise reset all.
        """
        if operation_name:
            self.operations[operation_name] = []
        else:
            self.operations.clear()
