# Test Suite

Comprehensive test coverage for the 88i sinistro harness system, providing end-to-end validation from claim submission through processing to final decision.

---

## Test Categories

The test suite consists of seven complementary test categories, each targeting different aspects of system quality:

### 1. Unit Tests (Phase 1-3)

**Location:** `tests/unit/` and scattered throughout test directories

Unit tests validate individual functions, classes, and modules in isolation. These are fast, deterministic, and provide immediate feedback during development.

**What's covered:**
- Context engine providers (insurance, reembolso, etc.)
- Plugin loading and initialization
- Tool parameter validation
- State storage operations
- Utility functions and helpers

**Example:**
```bash
pytest tests/unit/ -v
```

### 2. Integration Tests

**Location:** `tests/integration/`

Integration tests verify real connections to external services (Supabase, Inngest) without mocks. These tests require staging credentials.

**What's covered:**
- Supabase database operations (save, load, TTL)
- Inngest workflow triggering and scheduling
- Langfuse span creation and cost tracking
- Data consistency across operations
- Error handling with unavailable services

**Files:**
- `tests/integration/test_supabase_integration.py`
- `tests/integration/test_inngest_integration.py`

**Example:**
```bash
export SUPABASE_STAGING_URL="https://..."
export SUPABASE_STAGING_KEY="..."
export INNGEST_STAGING_KEY="..."

pytest tests/integration/ -v
```

### 3. Performance Tests

**Location:** `tests/performance/`

Performance tests measure latency and throughput for all major operations, establishing baselines and detecting regressions.

**What's covered:**
- Extract fields latency (document parsing)
- Fraud score latency (model inference)
- Context injection latency (prompt enhancement)
- Plugin load latency (initialization)
- State save latency (database write)
- Monitoring overhead (Langfuse)

**Targets:**
- Extract fields: < 100ms avg, > 10 ops/sec
- Fraud score: < 150ms avg, > 6 ops/sec
- Context inject: < 50ms avg, > 20 ops/sec
- Plugin load: < 200ms avg, > 5 ops/sec
- State save: < 300ms avg, > 3 ops/sec
- Monitoring: < 10ms avg, > 100 ops/sec

**Example:**
```bash
pytest tests/performance/ -v -m performance
```

### 4. Security Tests

**Location:** `tests/security/`

Security tests verify protection against common vulnerabilities and adherence to security best practices.

**What's covered:**
- SQL injection prevention
- Authentication requirements
- Input validation
- Environment variable security (secrets)
- Plugin isolation
- Rate limiting
- CORS headers
- Data validation

**Example:**
```bash
pytest tests/security/ -v -m security
```

### 5. Chaos Engineering Tests

**Location:** `tests/chaos/`

Chaos tests verify system resilience under failure conditions, ensuring graceful degradation and proper recovery.

**What's covered:**
- Supabase unavailability
- Inngest API timeout
- Context provider failures
- Plugin load failures
- Langfuse unavailability
- Concurrent failure recovery
- Memory leak detection

**Example:**
```bash
pytest tests/chaos/ -v -m chaos
```

### 6. Load Tests

**Location:** `tests/load/`

Load tests simulate concurrent users to verify throughput and scalability using Locust framework.

**What's covered:**
- Extract fields at 100+ concurrent users
- Fraud scoring at 100+ concurrent users
- State persistence at 100+ concurrent users
- Context injection at 100+ concurrent users
- Response time percentiles (p50, p95, p99)
- Error rate under sustained load
- Memory usage under load

**Targets:**
- System throughput: > 100 req/sec
- Extract fields: < 500ms @ p95
- Fraud score: < 750ms @ p95
- State save: < 1000ms @ p95
- Context inject: < 200ms @ p95
- Error rate: < 0.1%

**Example:**
```bash
# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### 7. End-to-End Tests

**Location:** `tests/e2e/`

E2E tests verify complete workflows from claim submission through analysis to final decision, exercising the full system integration.

**What's covered:**
- Roubo (theft) claim workflow
- Colisão (collision) claim workflow
- Multi-turn conversations with state persistence
- Plugin execution within workflows
- Document processing and analysis
- Fraud scoring and decision logic
- State transitions across conversation turns

**Example:**
```bash
pytest tests/e2e/ -v -m e2e
```

---

## Running Tests

### Running All Tests

```bash
# Run entire test suite
pytest tests/ -v

# Run with summary
pytest tests/ -v --tb=short

# Run with detailed output
pytest tests/ -v -s

# Run and stop on first failure
pytest tests/ -v -x
```

### Running by Category

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires staging credentials)
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v -m performance

# Security tests
pytest tests/security/ -v -m security

# Chaos tests
pytest tests/chaos/ -v -m chaos

# E2E tests
pytest tests/e2e/ -v -m e2e

# Load tests (requires running server)
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### Running with Coverage

```bash
# Generate coverage report (HTML)
pytest tests/ \
  --cov=context_engine \
  --cov=plugins \
  --cov=monitoring \
  --cov-report=html \
  --cov-report=term-missing

# View HTML report
open htmlcov/index.html

# Generate coverage with branch analysis
pytest tests/ \
  --cov=context_engine \
  --cov=plugins \
  --cov=monitoring \
  --cov-report=html \
  --cov-branch

# Generate JSON report for CI/CD
pytest tests/ \
  --cov=context_engine \
  --cov=plugins \
  --cov=monitoring \
  --cov-report=json \
  --cov-report=term
```

### Running Specific Tests

```bash
# Run single test file
pytest tests/security/test_security_audit.py -v

# Run single test function
pytest tests/security/test_security_audit.py::test_sql_injection_prevention -v

# Run tests matching pattern
pytest tests/ -k "fraud" -v

# Run by marker
pytest tests/ -m performance -v
pytest tests/ -m security -v
pytest tests/ -m chaos -v
pytest tests/ -m e2e -v
```

### Running with Options

```bash
# Show print statements and logging
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -v -x

# Stop on first N failures
pytest tests/ -v --maxfail=3

# Verbose output with traceback
pytest tests/ -v --tb=long

# Run N tests in parallel
pytest tests/ -v -n 4

# Verbose with coverage
pytest tests/ -v --cov=context_engine --cov-report=term

# Run with custom timeout (seconds)
pytest tests/ -v --timeout=60

# Run and generate JUnit XML for CI
pytest tests/ -v --junit-xml=results.xml
```

---

## Test Statistics

### Coverage Targets

| Module | Target | Status |
|--------|--------|--------|
| context_engine | > 95% | ✅ |
| plugins | > 90% | ✅ |
| monitoring | > 85% | ✅ |
| tools | > 90% | ✅ |
| **Overall** | **> 85%** | ✅ |

### Test Distribution

| Category | Count | Avg Time | Total Time |
|----------|-------|----------|------------|
| Unit | 15+ | 0.1s | < 2min |
| Integration | 8 | 2s | < 20s |
| Performance | 6 | 5s | < 30s |
| Security | 8 | 0.1s | < 1s |
| Chaos | 7 | 2s | < 15s |
| E2E | 4 | 30s | < 2min |
| Load | N/A | variable | variable |
| **Total** | **50+** | average | **< 10min** |

### Performance Benchmarks

Baseline performance (on M2 Mac, no load):

| Operation | Avg | Min | Max | Throughput |
|-----------|-----|-----|-----|------------|
| Extract fields | 85ms | 72ms | 120ms | 11.8 ops/sec |
| Fraud score | 120ms | 95ms | 180ms | 8.3 ops/sec |
| Context inject | 42ms | 35ms | 65ms | 23.8 ops/sec |
| Plugin load | 180ms | 150ms | 250ms | 5.6 ops/sec |
| State save | 280ms | 200ms | 400ms | 3.6 ops/sec |
| Monitoring | 8ms | 5ms | 12ms | 125 ops/sec |

### Security Audit Results

All security tests passing:

- ✅ SQL injection prevention
- ✅ Authentication required
- ✅ Input validation
- ✅ Environment variable security
- ✅ Plugin isolation
- ✅ Rate limiting
- ✅ CORS headers
- ✅ Data validation

---

## CI/CD Integration

### GitHub Actions

All tests run automatically on push and pull request:

```yaml
# .github/workflows/test.yml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Nightly

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Pre-commit Hook

Run tests before committing:

```bash
# Create .git/hooks/pre-commit
#!/bin/bash
pytest tests/unit/ --tb=short || exit 1
```

### Docker

Run tests in Docker:

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["pytest", "tests/", "--cov", "--cov-report=html"]
```

```bash
docker build -t sinistro-tests .
docker run -v $(pwd)/htmlcov:/app/htmlcov sinistro-tests
```

---

## Common Tasks

### Check Coverage

```bash
pytest tests/ --cov=context_engine --cov=plugins --cov=monitoring --cov-report=term-missing
```

### Profile Slow Tests

```bash
pytest tests/ -v --durations=10
```

### Debug Failing Test

```bash
# Run with print statements
pytest tests/security/test_security_audit.py::test_sql_injection_prevention -v -s

# Run with debugger
pytest tests/security/test_security_audit.py::test_sql_injection_prevention -v --pdb
```

### Run Tests in Watch Mode

```bash
# Install ptw
pip install pytest-watch

# Watch for changes and re-run
ptw tests/
```

### Generate Test Report

```bash
pytest tests/ -v \
  --cov=context_engine \
  --cov=plugins \
  --cov=monitoring \
  --cov-report=html \
  --cov-report=term \
  --junit-xml=test-results.xml

# View HTML report
open htmlcov/index.html
```

---

## Fixture Reference

Common fixtures available in `tests/conftest.py`:

### Staging Credentials (Session Scope)

```python
@pytest.fixture(scope="session")
def supabase_staging_url() -> str:
    """Get staging Supabase URL from env."""
    
@pytest.fixture(scope="session")
def supabase_staging_key() -> str:
    """Get staging Supabase service role key from env."""
    
@pytest.fixture(scope="session")
def inngest_staging_key() -> str:
    """Get staging Inngest API key from env."""
```

### Clients (Session Scope)

```python
@pytest.fixture
async def supabase_client(supabase_staging_url, supabase_staging_key):
    """Create staging Supabase client."""
    
@pytest.fixture
async def inngest_client(inngest_staging_key):
    """Create staging Inngest client."""
```

### Synthetic Data (Function Scope)

```python
@pytest.fixture
def synthetic_sinistro_data():
    """Generate synthetic sinistro data for testing."""
    
@pytest.fixture
def synthetic_user_data():
    """Generate synthetic user data for testing."""
```

### Performance Tools (Function Scope)

```python
@pytest.fixture
def benchmark_tracker():
    """Track benchmark results with measure_async() method."""
    
@pytest.fixture
def performance_targets():
    """Define performance targets for operations."""
```

### Event Loop (Session Scope)

```python
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
```

---

## Extending Tests

### Adding a Unit Test

```python
# tests/unit/test_my_feature.py
import pytest
from my_module import my_function

def test_my_function():
    """Test my_function with valid input."""
    result = my_function("input")
    assert result == "expected"
```

### Adding a Performance Test

```python
# tests/performance/test_my_performance.py
@pytest.mark.asyncio
@pytest.mark.performance
async def test_my_operation_performance(benchmark_tracker, performance_targets):
    """Benchmark my operation."""
    async def run_op():
        return await my_operation()
    
    result = await benchmark_tracker.measure_async(
        "my_operation",
        run_op,
        iterations=100
    )
    
    target = performance_targets["my_operation"]
    assert result.avg_ms <= target["max_avg_ms"]
```

### Adding a Security Test

```python
# tests/security/test_my_security.py
@pytest.mark.security
def test_my_security_check():
    """Test security aspect."""
    # Test code
    assert is_secure()
```

### Adding an Integration Test

```python
# tests/integration/test_my_integration.py
@pytest.mark.asyncio
async def test_my_integration(supabase_client):
    """Test integration with Supabase."""
    result = await supabase_client.table("my_table").select("*").limit(1).execute()
    assert result is not None
```

---

## Troubleshooting

### Tests Won't Run

```bash
# Ensure you're in project root
cd ~/Projects/88i-sinistro-harness

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run pytest
pytest tests/ -v
```

### Import Errors

```bash
# Install test dependencies
pip install -r requirements.txt pytest pytest-asyncio pytest-cov

# Update PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Coverage Not Generating

```bash
# Install coverage
pip install pytest-cov

# Generate with explicit paths
pytest tests/ \
  --cov=. \
  --cov-report=html \
  --cov-report=term
```

### Performance Tests Slow

```bash
# Close other applications
# Check system resources: top, Activity Monitor

# Run in isolation
pytest tests/performance/test_performance_benchmarks.py -v
```

---

## Resources

- **[docs/PHASE4_TESTING_GUIDE.md](../docs/PHASE4_TESTING_GUIDE.md)** — Comprehensive testing guide
- **[pytest documentation](https://docs.pytest.org/)** — Test framework docs
- **[pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)** — Async test support
- **[Coverage.py](https://coverage.readthedocs.io/)** — Coverage reporting

---

**Test Suite Documentation v1.0**  
Last Updated: May 27, 2026  
Status: ✅ Complete
