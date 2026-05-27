# Performance Optimization & SLA Validation Guide

## Overview

This document provides comprehensive guidance on performance optimization, SLA targets, and best practices for the 88i Sinistro Harness system. The system implements performance monitoring, caching strategies, and optimization techniques to ensure reliability and responsiveness.

## SLA Targets

The following SLA targets have been established for core operation types. These targets represent the 95th percentile (P95) latency threshold that should not be exceeded:

| Operation Type | Target Latency (ms) | Description |
|---|---|---|
| **extract** | 100 | Document/data extraction operations |
| **fraud** | 150 | Fraud detection and analysis |
| **context** | 50 | Context retrieval and enrichment |
| **plugin** | 200 | Plugin execution and integration |
| **state** | 300 | State management operations |
| **monitoring** | 10 | Monitoring/metrics collection |

### SLA Targets Rationale

- **context** (50ms): Lowest target as context is foundational and frequently accessed
- **monitoring** (10ms): Ultra-low target for observability to minimize overhead
- **extract** (100ms): Moderate target for extraction operations
- **fraud** (150ms): Moderate-high target for fraud detection
- **plugin** (200ms): Higher target allowing for plugin execution variability
- **state** (300ms): Highest target for stateful operations that may involve more processing

## Performance Monitoring

### PerformanceOptimizer Class

The `PerformanceOptimizer` class (`app/performance.py`) provides comprehensive latency tracking and SLA validation:

```python
from app.performance import PerformanceOptimizer, TARGET_LATENCIES

# Initialize optimizer
optimizer = PerformanceOptimizer(target_latencies=TARGET_LATENCIES)

# Track operation latency (decorator)
@optimizer.track_operation("extract")
def extract_data(document):
    # Extraction logic
    pass

# Get performance report
report = optimizer.get_report("extract")
# Returns: {
#   "count": 100,
#   "min": 15.2,
#   "max": 98.5,
#   "mean": 45.3,
#   "p50": 42.1,
#   "p95": 87.3,
#   "p99": 96.2,
#   "target": 100,
#   "sla_breaches": 0,
#   "compliance_pct": 100.0
# }
```

### Decorator for Async and Sync Functions

The `track_operation` decorator automatically handles both async and sync functions:

```python
optimizer = PerformanceOptimizer()

# Sync function
@optimizer.track_operation("fraud_check")
def check_fraud(claim):
    # Synchronous processing
    return is_fraudulent

# Async function
@optimizer.track_operation("async_extract")
async def async_extract(document):
    # Asynchronous processing
    return extracted_data

# Both track latency automatically
```

### Percentile Calculations

The optimizer supports percentile calculation for performance analysis:

```python
# Get specific percentiles
p50 = optimizer.get_percentile("extract", 50)  # Median
p95 = optimizer.get_percentile("extract", 95)  # 95th percentile
p99 = optimizer.get_percentile("extract", 99)  # 99th percentile
```

### Performance Reports

Get comprehensive reports for all operations:

```python
# Single operation report
report = optimizer.get_report("extract")

# All operations report
all_reports = optimizer.get_all_reports()
for op_name, metrics in all_reports.items():
    print(f"{op_name}: P95={metrics['p95']:.2f}ms, Compliance={metrics['compliance_pct']:.1f}%")
```

## Caching Strategies

### CacheManager Overview

The `CacheManager` class (`app/caching.py`) provides unified caching with Redis and in-memory fallback:

```python
from app.caching import CacheManager

# Initialize with Redis (optional)
cache_manager = CacheManager(redis_url="redis://localhost:6379/0")

# Or use in-memory cache only
cache_manager = CacheManager()

# Basic cache operations
cache_manager.set("key", {"data": "value"}, ttl=3600)
value = cache_manager.get("key")
cache_manager.delete("key")
cache_manager.clear()
```

### Cache Patterns

#### 1. Context Caching

Cache enriched context for frequently accessed entities:

```python
@cache_manager.cache_decorator(ttl=1800, key_prefix="context:")
def get_context(entity_id: str):
    # Expensive context retrieval
    context = retrieve_context_data(entity_id)
    return context

# First call: expensive
context = get_context("entity_123")  # Cache miss, computes and stores

# Subsequent calls: fast
context = get_context("entity_123")  # Cache hit, returns immediately
```

#### 2. Extract Result Caching

Cache document extraction results during processing:

```python
@cache_manager.cache_decorator(ttl=3600, key_prefix="extract:")
def extract_document_fields(document_id: str):
    # Extract fields from document
    fields = extract_fields(document_id)
    return fields
```

#### 3. Fraud Detection Caching

Cache fraud signals and historical patterns:

```python
cache_manager.set(f"fraud:signals:{claim_id}", signals, ttl=7200)
cached_signals = cache_manager.get(f"fraud:signals:{claim_id}")
```

#### 4. Pattern-Based Invalidation

Clear cache by pattern when updates occur:

```python
# Clear all user context when profile changes
cache_manager.delete_pattern("context:user:*")

# Clear all fraud signals for a claim when status changes
cache_manager.delete_pattern(f"fraud:signals:{claim_id}:*")
```

### Redis Configuration

For production deployment with Redis:

```python
import os
from app.caching import CacheManager

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
cache_manager = CacheManager(redis_url=redis_url)
```

### Graceful Degradation

The cache manager automatically falls back to in-memory caching if Redis becomes unavailable:

```python
# Attempts Redis first
# Falls back to in-memory if Redis connection fails
# All cache operations work seamlessly in both modes
cache_manager.set("key", "value", ttl=3600)
```

## Async Processing

### Async Operation Optimization

Use async operations for I/O-bound tasks:

```python
import asyncio
from app.performance import PerformanceOptimizer

optimizer = PerformanceOptimizer()

@optimizer.track_operation("async_extract")
async def async_extract_batch(documents: List[str]):
    """Process documents concurrently."""
    tasks = [extract_document(doc) for doc in documents]
    results = await asyncio.gather(*tasks)
    return results
```

### Concurrent Operations

Process multiple operations concurrently for better throughput:

```python
async def process_claim_async(claim_id: str):
    # Run extract, fraud check, and context enrichment concurrently
    extract_task = async_extract(claim_data)
    fraud_task = check_fraud_async(claim_data)
    context_task = enrich_context_async(claim_data)
    
    results = await asyncio.gather(
        extract_task, fraud_task, context_task
    )
    return results
```

## Database Optimization

### Indexing Strategy

Ensure key tables have appropriate indexes for common queries:

```sql
-- Fast lookups by operation type
CREATE INDEX idx_operation_type ON operations(operation_type);

-- Time-range queries
CREATE INDEX idx_operation_timestamp ON operations(timestamp DESC);

-- Composite indexes for common queries
CREATE INDEX idx_claim_status_date ON claims(status, created_at DESC);
```

### Query Optimization

- Use connection pooling for database connections
- Implement read replicas for read-heavy queries
- Use prepared statements to avoid query parsing overhead
- Batch insert/update operations where possible

### Caching Database Queries

Cache frequently accessed data:

```python
@cache_manager.cache_decorator(ttl=1800, key_prefix="claim:")
def get_claim_details(claim_id: str):
    # Query database
    return db.query(Claim).filter_by(id=claim_id).first()
```

## Tuning Checklist

### Pre-Deployment Optimization

- [ ] Run SLA validation tests (tests/performance/test_sla_validation.py)
- [ ] Verify all operation types meet P95 targets
- [ ] Check cache hit rates in staging environment
- [ ] Profile hot code paths with performance tools
- [ ] Review database query execution plans
- [ ] Test async operation concurrency limits

### Monitoring and Alerting

- [ ] Set up performance monitoring dashboard
- [ ] Configure alerts for SLA breaches (compliance < 95%)
- [ ] Monitor cache hit ratios (target: > 80%)
- [ ] Track Redis connection health
- [ ] Monitor memory usage in fallback cache mode

### Production Tuning

- [ ] Adjust cache TTL based on data update frequency
- [ ] Monitor and optimize database indexes
- [ ] Configure connection pool sizes for load
- [ ] Set appropriate async concurrency limits
- [ ] Implement circuit breakers for external services

### Performance Baselines

Establish performance baselines for each operation type:

```python
# Run baseline tests
pytest tests/performance/test_sla_validation.py -v

# Expected baselines:
# - extract: P95 < 100ms (baseline: ~87ms)
# - fraud: P95 < 150ms (baseline: ~130ms)
# - context: P95 < 50ms (baseline: ~42ms)
# - plugin: P95 < 200ms (baseline: ~175ms)
# - state: P95 < 300ms (baseline: ~280ms)
```

## Integration with Main Application

The performance optimizer is integrated into the main application:

```python
# In main.py
from app.performance import PerformanceOptimizer, TARGET_LATENCIES

# Initialize at startup
optimizer = PerformanceOptimizer(target_latencies=TARGET_LATENCIES)

# Expose metrics endpoint
@app.get("/metrics/performance")
async def get_performance_metrics():
    """Return current performance metrics for all operations."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "operations": optimizer.get_all_reports(),
        "timestamp": datetime.utcnow().isoformat(),
    }
```

## Best Practices

### 1. Selective Caching
Only cache data that:
- Takes significant time to compute
- Is accessed frequently
- Changes infrequently

### 2. TTL Selection
- **Short-lived data** (minutes): user sessions, temporary state
- **Medium-lived data** (hours): user context, extracted fields
- **Long-lived data** (days): reference data, fraud patterns

### 3. Error Handling
Always handle cache failures gracefully:

```python
try:
    cached_value = cache_manager.get(key)
    if cached_value:
        return cached_value
except Exception as e:
    logger.warning(f"Cache error: {e}")
    # Fall through to compute value

# Compute and optionally cache
value = compute_value()
try:
    cache_manager.set(key, value, ttl=3600)
except Exception as e:
    logger.warning(f"Failed to cache value: {e}")
    # Continue without caching

return value
```

### 4. Monitoring Performance
Regularly review performance metrics:

```python
# Get performance summary
all_reports = optimizer.get_all_reports()
for op_name, report in all_reports.items():
    if report["compliance_pct"] < 95:
        logger.warning(
            f"Operation '{op_name}' SLA breach: "
            f"Compliance {report['compliance_pct']:.1f}% < 95%"
        )
```

## Troubleshooting

### High Latency

1. Check cache hit ratios - add caching if low
2. Profile code to identify bottlenecks
3. Review database query execution plans
4. Check external service response times
5. Monitor system resources (CPU, memory, I/O)

### Cache Issues

1. Verify Redis connection with `redis-cli ping`
2. Check cache memory usage
3. Review cache TTL settings
4. Monitor eviction policies
5. Validate cache key patterns

### SLA Breaches

1. Run `pytest tests/performance/test_sla_validation.py -v`
2. Check server load and resource utilization
3. Review recent code changes for regressions
4. Analyze P95 and P99 percentiles for outliers
5. Adjust targets if consistently exceeded

## References

- Performance Optimization Class: `app/performance.py`
- Cache Manager Class: `app/caching.py`
- SLA Validation Tests: `tests/performance/test_sla_validation.py`
- Main Application: `main.py` - Performance metrics endpoint
- Performance Benchmarks: `tests/performance/test_performance_benchmarks.py`
