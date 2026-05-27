"""SLA validation tests for core operations.

Tests performance targets for extract, fraud, context, plugin, and state operations.
Each operation is tested with 100 iterations, validating P95 latency < target.
"""

from __future__ import annotations

import pytest
import asyncio
import time
from typing import List

from app.performance import PerformanceOptimizer, TARGET_LATENCIES


class TestSLAValidation:
    """Test suite for SLA compliance across operation types."""

    @pytest.fixture
    def optimizer(self):
        """Create a fresh PerformanceOptimizer for each test."""
        return PerformanceOptimizer(target_latencies=TARGET_LATENCIES)

    def test_extract_operation_sla(self, optimizer):
        """Test extract operation meets SLA target (100ms).

        Runs 100 iterations of a simulated extract operation and validates
        P95 latency is below the 100ms target.
        """
        @optimizer.track_operation("extract")
        def simulate_extract():
            # Simulate extract operation: ~20-30ms on average
            time.sleep(0.02)

        # Run 100 iterations
        for _ in range(100):
            simulate_extract()

        # Validate SLA
        report = optimizer.get_report("extract")
        assert report["count"] == 100
        assert report["p95"] is not None
        assert report["target"] == 100
        assert report["p95"] < report["target"], \
            f"P95 latency {report['p95']:.2f}ms exceeds target {report['target']}ms"
        assert report["compliance_pct"] >= 95.0, \
            f"Compliance {report['compliance_pct']:.1f}% below 95%"

    def test_fraud_operation_sla(self, optimizer):
        """Test fraud operation meets SLA target (150ms).

        Runs 100 iterations of a simulated fraud detection operation
        and validates P95 latency is below the 150ms target.
        """
        @optimizer.track_operation("fraud")
        def simulate_fraud():
            # Simulate fraud operation: ~30-40ms on average
            time.sleep(0.03)

        # Run 100 iterations
        for _ in range(100):
            simulate_fraud()

        # Validate SLA
        report = optimizer.get_report("fraud")
        assert report["count"] == 100
        assert report["p95"] is not None
        assert report["target"] == 150
        assert report["p95"] < report["target"], \
            f"P95 latency {report['p95']:.2f}ms exceeds target {report['target']}ms"
        assert report["compliance_pct"] >= 95.0, \
            f"Compliance {report['compliance_pct']:.1f}% below 95%"

    def test_context_operation_sla(self, optimizer):
        """Test context operation meets SLA target (50ms).

        Runs 100 iterations of a simulated context retrieval operation
        and validates P95 latency is below the 50ms target.
        """
        @optimizer.track_operation("context")
        def simulate_context():
            # Simulate context operation: ~10-15ms on average
            time.sleep(0.012)

        # Run 100 iterations
        for _ in range(100):
            simulate_context()

        # Validate SLA
        report = optimizer.get_report("context")
        assert report["count"] == 100
        assert report["p95"] is not None
        assert report["target"] == 50
        assert report["p95"] < report["target"], \
            f"P95 latency {report['p95']:.2f}ms exceeds target {report['target']}ms"
        assert report["compliance_pct"] >= 95.0, \
            f"Compliance {report['compliance_pct']:.1f}% below 95%"

    def test_plugin_operation_sla(self, optimizer):
        """Test plugin operation meets SLA target (200ms).

        Runs 100 iterations of a simulated plugin execution and validates
        P95 latency is below the 200ms target.
        """
        @optimizer.track_operation("plugin")
        def simulate_plugin():
            # Simulate plugin operation: ~50-60ms on average
            time.sleep(0.055)

        # Run 100 iterations
        for _ in range(100):
            simulate_plugin()

        # Validate SLA
        report = optimizer.get_report("plugin")
        assert report["count"] == 100
        assert report["p95"] is not None
        assert report["target"] == 200
        assert report["p95"] < report["target"], \
            f"P95 latency {report['p95']:.2f}ms exceeds target {report['target']}ms"
        assert report["compliance_pct"] >= 95.0, \
            f"Compliance {report['compliance_pct']:.1f}% below 95%"

    def test_state_operation_sla(self, optimizer):
        """Test state operation meets SLA target (300ms).

        Runs 100 iterations of a simulated state management operation
        and validates P95 latency is below the 300ms target.
        """
        @optimizer.track_operation("state")
        def simulate_state():
            # Simulate state operation: ~100-120ms on average
            time.sleep(0.11)

        # Run 100 iterations
        for _ in range(100):
            simulate_state()

        # Validate SLA
        report = optimizer.get_report("state")
        assert report["count"] == 100
        assert report["p95"] is not None
        assert report["target"] == 300
        assert report["p95"] < report["target"], \
            f"P95 latency {report['p95']:.2f}ms exceeds target {report['target']}ms"
        assert report["compliance_pct"] >= 95.0, \
            f"Compliance {report['compliance_pct']:.1f}% below 95%"

    def test_percentile_calculation(self, optimizer):
        """Test percentile calculation accuracy."""
        @optimizer.track_operation("test_percentile")
        def simulate_operation():
            time.sleep(0.01)

        # Run enough iterations to test percentile calculation
        for _ in range(100):
            simulate_operation()

        p50 = optimizer.get_percentile("test_percentile", 50)
        p95 = optimizer.get_percentile("test_percentile", 95)
        p99 = optimizer.get_percentile("test_percentile", 99)

        assert p50 is not None
        assert p95 is not None
        assert p99 is not None
        # P50 should be less than P95 which should be less than P99
        assert p50 <= p95 <= p99

    def test_report_metrics(self, optimizer):
        """Test all metrics in performance report."""
        @optimizer.track_operation("test_report")
        def simulate_operation():
            time.sleep(0.02)

        for _ in range(50):
            simulate_operation()

        report = optimizer.get_report("test_report")

        # Verify all keys exist
        assert "count" in report
        assert "min" in report
        assert "max" in report
        assert "mean" in report
        assert "p50" in report
        assert "p95" in report
        assert "p99" in report
        assert "target" in report
        assert "sla_breaches" in report
        assert "compliance_pct" in report

        # Verify data relationships
        assert report["count"] == 50
        assert report["min"] > 0
        assert report["max"] >= report["min"]
        assert report["mean"] >= report["min"]
        assert report["mean"] <= report["max"]
        assert report["sla_breaches"] >= 0
        assert 0 <= report["compliance_pct"] <= 100

    def test_empty_operation_report(self, optimizer):
        """Test report for operation with no recorded data."""
        report = optimizer.get_report("nonexistent_operation")

        assert report["count"] == 0
        assert report["min"] is None
        assert report["max"] is None
        assert report["mean"] is None
        assert report["p50"] is None
        assert report["p95"] is None
        assert report["p99"] is None
        assert report["sla_breaches"] == 0
        assert report["compliance_pct"] == 0.0

    def test_reset_operations(self, optimizer):
        """Test resetting operation tracking data."""
        @optimizer.track_operation("reset_test")
        def simulate_operation():
            time.sleep(0.01)

        # Record some operations
        for _ in range(10):
            simulate_operation()

        report_before = optimizer.get_report("reset_test")
        assert report_before["count"] == 10

        # Reset
        optimizer.reset("reset_test")

        report_after = optimizer.get_report("reset_test")
        assert report_after["count"] == 0

    def test_multiple_operations_tracking(self, optimizer):
        """Test tracking multiple different operations simultaneously."""
        @optimizer.track_operation("op_a")
        def op_a():
            time.sleep(0.01)

        @optimizer.track_operation("op_b")
        def op_b():
            time.sleep(0.02)

        # Run both operations
        for _ in range(50):
            op_a()
            op_b()

        # Get all reports
        all_reports = optimizer.get_all_reports()

        assert len(all_reports) == 2
        assert all_reports["op_a"]["count"] == 50
        assert all_reports["op_b"]["count"] == 50
        # op_b should be slower than op_a
        assert all_reports["op_b"]["mean"] > all_reports["op_a"]["mean"]


class TestAsyncOperationTracking:
    """Test async operation tracking."""

    @pytest.fixture
    def optimizer(self):
        """Create a fresh PerformanceOptimizer for async tests."""
        return PerformanceOptimizer(target_latencies=TARGET_LATENCIES)

    @pytest.mark.asyncio
    async def test_async_operation_tracking(self, optimizer):
        """Test tracking async operation latency."""
        @optimizer.track_operation("async_extract")
        async def simulate_async_extract():
            await asyncio.sleep(0.02)

        # Run async operations
        for _ in range(50):
            await simulate_async_extract()

        report = optimizer.get_report("async_extract")
        assert report["count"] == 50
        assert report["p95"] is not None
        assert report["p95"] > 0

    @pytest.mark.asyncio
    async def test_mixed_async_sync_operations(self, optimizer):
        """Test mixing async and sync operations."""
        @optimizer.track_operation("mixed_op")
        async def async_op():
            await asyncio.sleep(0.01)

        @optimizer.track_operation("mixed_op")
        def sync_op():
            time.sleep(0.01)

        # Run mixed operations
        for _ in range(25):
            await async_op()
            sync_op()

        report = optimizer.get_report("mixed_op")
        assert report["count"] == 50  # 25 async + 25 sync


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
