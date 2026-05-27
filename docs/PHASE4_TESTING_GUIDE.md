# Phase 4: Comprehensive Testing Guide

## Overview

Phase 4 provides comprehensive test coverage across all components of the 88i sinistro harness system:

- **Integration tests** — Real connections to staging Supabase, Inngest, and Langfuse
- **Performance benchmarking** — Latency and throughput targets for all operations
- **Security audit** — SQL injection prevention, authentication, input validation, and secrets protection
- **Chaos engineering** — Failure scenarios, resilience testing, and recovery validation
- **Load testing** — Concurrent user simulation and scalability verification
- **End-to-end workflows** — Complete claim processing from submission to decision
- **Documentation** — Comprehensive guide and coverage reporting

This guide covers test categories, how to run each category, performance targets, security checklist, troubleshooting, and next steps.

---

## Test Categories

### 1. Integration Tests

**Location:** `tests/integration/`

Integration tests verify real connections to staging services without mocks. These tests are critical for validating that the system works with actual external APIs.

**What's tested:**
- Supabase state persistence (save/load/TTL)
- Concurrent state writes under load
- Inngest workflow triggering and scheduling
- Error handling with unavailable services
- Data consistency across multiple operations

**Files:**
- `tests/integration/test_supabase_integration.py` — Supabase operations
- `tests/integration/test_inngest_integration.py` — Inngest workflows
- `tests/conftest.py` — Shared fixtures for staging credentials

**Prerequisites:**
```bash
export SUPABASE_STAGING_URL="https://your-staging-supabase.url"
export SUPABASE_STAGING_KEY="your-staging-service-key"
export INNGEST_STAGING_KEY="your-staging-inngest-key"
```

**How to run:**
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run only Supabase tests
pytest tests/integration/test_supabase_integration.py -v

# Run only Inngest tests
pytest tests/integration/test_inngest_integration.py -v

# Run with markers
pytest tests/ -m integration -v
```

**Test coverage:**
- Connection validation
- State save and load operations
- TTL expiration handling
- Concurrent write safety
- Error handling and degradation
- Transaction rollback on failure

**Expected results:**
- All tests pass with real staging credentials
- Tests skip gracefully if credentials missing
- No data corruption in staging database
- Performance within acceptable bounds (< 1s per operation)

---

### 2. Performance Tests

**Location:** `tests/performance/`

Performance tests measure operation latency and throughput to ensure the system meets performance targets. These tests establish baseline metrics and detect performance regressions.

**What's tested:**
- Extract fields operation (document parsing, field detection)
- Fraud scoring (model inference, risk calculation)
- Context injection (prompt enhancement, provider lookup)
- Plugin loading (initialization, dependency resolution)
- State persistence (database write latency)
- Monitoring overhead (Langfuse span creation)

**Files:**
- `tests/performance/test_performance_benchmarks.py` — All performance tests
- `tests/performance/conftest.py` — Benchmark fixtures and utilities

**Performance Targets Table:**

| Operation | Max Avg Latency | Min Throughput | Notes |
|-----------|-----------------|----------------|-------|
| Extract fields | 100 ms | 10 ops/sec | Document parsing with LLM |
| Fraud score | 150 ms | 6 ops/sec | Model inference with context |
| Context inject | 50 ms | 20 ops/sec | In-memory context enhancement |
| Plugin load | 200 ms | 5 ops/sec | First-time plugin discovery |
| State save | 300 ms | 3 ops/sec | Database write with TTL |
| Monitoring trace | 10 ms | 100 ops/sec | Span creation (non-blocking) |

**How to run:**
```bash
# Run all performance tests
pytest tests/performance/ -v -m performance

# Run with verbose output and detailed stats
pytest tests/performance/test_performance_benchmarks.py -v -s

# Run single test
pytest tests/performance/test_performance_benchmarks.py::test_extract_fields_performance -v
```

**Interpreting results:**
- **avg_ms** — Average latency per operation (should be below max)
- **throughput** — Operations per second (should be above minimum)
- **min_ms** — Fastest execution time (indicates best-case performance)
- **max_ms** — Slowest execution time (indicates outliers)

**Example output:**
```
extract_fields:
  Iterations:  50
  Total Time:  4500.25 ms
  Avg:         90.00 ms
  Min:         75.20 ms
  Max:         125.30 ms
  Throughput:  11.11 ops/sec
✓ PASS: avg_ms (90.00) <= target (100.00)
✓ PASS: throughput (11.11) >= target (10.00)
```

**Performance optimization tips:**
- Run tests on isolated machine (no other processes)
- Check system CPU/memory availability
- Run multiple times to get stable average
- Profile slow operations with `cProfile` or `py-spy`
- Consider network latency for Supabase tests

---

### 3. Security Tests

**Location:** `tests/security/`

Security tests verify the system is protected against common vulnerabilities and follows security best practices. These tests should run in every CI/CD pipeline.

**What's tested:**
- SQL injection prevention (parameterized queries)
- Authentication requirements (no unauthorized access)
- Input validation (reject invalid data)
- Environment variable security (secrets not in logs)
- Plugin isolation (cannot escape sandboxes)
- Rate limiting considerations (async concurrency)
- CORS headers (if applicable)
- Data validation (type checking, bounds)

**Files:**
- `tests/security/test_security_audit.py` — All security tests

**Security Checklist:**

- ✅ **SQL Injection** — All Supabase queries use parameterized SDK
  - Test: `test_sql_injection_prevention()`
  - Validates: Escaping of user input in queries
  
- ✅ **Authentication** — Operations require valid credentials
  - Test: `test_authentication_required()`
  - Validates: No unauthenticated database access
  
- ✅ **Input Validation** — All user inputs validated before use
  - Test: `test_input_validation()`
  - Validates: Empty strings, None, XSS attempts, binary data handled

- ✅ **Secrets Protection** — API keys/passwords not logged
  - Test: `test_environment_variable_security()`
  - Validates: Secrets redacted from logs

- ✅ **Plugin Isolation** — Plugins cannot access global state
  - Test: `test_plugin_isolation()`
  - Validates: Proper plugin sandboxing

- ✅ **Rate Limiting** — Operations use async to avoid blocking
  - Test: `test_rate_limiting_prevention()`
  - Validates: Async/await patterns used

- ✅ **CORS** — HTTP endpoints have proper CORS headers
  - Test: `test_cors_headers()`
  - Validates: Not vulnerable to CSRF attacks

- ✅ **Data Validation** — Type validation on sensitive fields
  - Test: `test_data_validation()`
  - Validates: sinistro_tipo, veiculo_tipo, etc. restricted

**How to run:**
```bash
# Run all security tests
pytest tests/security/ -v -m security

# Run single security test
pytest tests/security/test_security_audit.py::test_sql_injection_prevention -v

# Run all tests marked security
pytest -m security -v
```

**Interpreting results:**
```
test_sql_injection_prevention PASSED
test_authentication_required PASSED
test_input_validation PASSED
test_environment_variable_security PASSED
test_plugin_isolation PASSED
test_rate_limiting_prevention PASSED
test_cors_headers PASSED
test_data_validation PASSED

========== 8 passed in 0.45s ==========
✓ No security vulnerabilities detected
```

**Vulnerability severity levels:**
- **Critical** — Immediate exploitation possible (SQL injection)
- **High** — Can compromise system (auth bypass)
- **Medium** — Potential data exposure (unvalidated input)
- **Low** — Defense-in-depth issue (header validation)

---

### 4. Chaos Engineering Tests

**Location:** `tests/chaos/`

Chaos tests verify system resilience under failure conditions. These tests ensure graceful degradation and proper error handling when external services become unavailable.

**What's tested:**
- Supabase unavailability (database offline)
- Inngest API timeout (workflow service slow)
- Context provider failure (plugin initialization error)
- Plugin load failure (missing dependencies)
- Langfuse monitoring unavailable (observability offline)
- Concurrent operation failure recovery
- Memory leak detection under load

**Files:**
- `tests/chaos/test_failure_scenarios.py` — All chaos tests

**Failure scenarios:**

| Scenario | Expected Behavior | Test |
|----------|-------------------|------|
| Supabase unavailable | Return False, don't crash | `test_supabase_unavailable()` |
| Inngest timeout | Return error dict, retry logic | `test_inngest_api_timeout()` |
| Context provider error | Use fallback context | `test_context_provider_failure()` |
| Plugin load fails | Continue without plugin | `test_plugin_load_failure()` |
| Langfuse offline | Degrade monitoring gracefully | `test_langfuse_unavailable()` |
| Concurrent failures | Continue with partial success | `test_concurrent_failure_recovery()` |
| Memory leak | < 50MB increase per 1000 ops | `test_memory_leak_under_load()` |

**How to run:**
```bash
# Run all chaos tests
pytest tests/chaos/ -v -m chaos

# Run single chaos scenario
pytest tests/chaos/test_failure_scenarios.py::test_supabase_unavailable -v

# Run with detailed output
pytest tests/chaos/ -v -s
```

**Interpreting results:**
```
test_supabase_unavailable PASSED (gracefully returned False)
test_inngest_api_timeout PASSED (returned error dict)
test_context_provider_failure PASSED (used fallback)
test_plugin_load_failure PASSED (continued without plugin)
test_langfuse_unavailable PASSED (monitoring degraded)
test_concurrent_failure_recovery PASSED (partial success)
test_memory_leak_under_load PASSED (50MB increase OK)

========== 7 passed in 12.34s ==========
✓ All failure scenarios handled gracefully
```

**Recovery expectations:**
- **Fast recovery** — System should resume within seconds
- **Partial success** — Continue with available services
- **No data loss** — All successful operations persisted
- **Clear error messages** — Logs indicate what failed
- **Automatic retry** — Transient failures retry automatically
- **Circuit breaker** — Stop retrying if persistent failure

---

### 5. Load Tests

**Location:** `tests/load/`

Load tests simulate concurrent users to verify system throughput and scalability. These tests identify bottlenecks and ensure performance under realistic load.

**What's tested:**
- Extract fields endpoint (document parsing at scale)
- Fraud score endpoint (model inference concurrency)
- State save endpoint (database write throughput)
- Context injection endpoint (provider performance)
- Overall system throughput (requests per second)
- Response time percentiles (p50, p95, p99)
- Error rate under load
- Memory usage under sustained load

**Files:**
- `tests/load/locustfile.py` — Load test configuration
- `tests/load/README.md` — Load testing documentation

**Performance targets:**

| Metric | Target | Notes |
|--------|--------|-------|
| Extract fields | < 500ms @ p95 | Document parsing |
| Fraud score | < 750ms @ p95 | Model inference |
| State save | < 1000ms @ p95 | Database write |
| Context inject | < 200ms @ p95 | In-memory operation |
| System throughput | > 100 req/sec | Total capacity |
| Error rate | < 0.1% | Reliability |

**Prerequisites:**
```bash
# Install Locust
pip install locust

# Start the agent server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**How to run:**
```bash
# Interactive web UI (recommended)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode with specific parameters
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --headless

# Run with custom CSV output
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 2m \
  --headless \
  --csv=results/load_test
```

**Interpreting results:**

Web UI shows:
- **Type** — Request type (POST /tools/sinistro_extract_fields)
- **Name** — Endpoint name
- **Requests** — Total requests completed
- **Failures** — Failed requests count
- **Median** — 50th percentile response time
- **95%ile** — 95th percentile response time
- **99%ile** — 99th percentile response time
- **Min/Max** — Minimum/maximum response times
- **Average** — Mean response time
- **RPS** — Requests per second

**CSV output example:**
```
Type,Name,Requests,Failures,Median,Mean,Min,Max,Content-Size,Requests/s
POST,/tools/sinistro_extract_fields,5000,5,150,175,85,450,2000,50.0
POST,/tools/sinistro_fraud_score,4800,3,200,220,90,650,1500,48.0
POST,/tools/langraph_save_state,4900,8,400,420,150,1200,800,49.0
POST,/tools/context_inject,5100,2,100,120,50,300,2500,51.0
```

**Load testing best practices:**
1. **Baseline first** — Run with 10 users to establish baseline
2. **Gradual ramp** — Increase users gradually (10, 25, 50, 100)
3. **Sustained load** — Run for 5+ minutes at each level
4. **Real scenarios** — Use realistic request distribution
5. **Monitor system** — Watch CPU/memory during test
6. **Analyze failures** — Investigate error causes
7. **Document results** — Keep baseline for comparison

---

### 6. End-to-End Tests

**Location:** `tests/e2e/`

End-to-end tests verify complete workflows from claim submission to final decision. These tests exercise the full system integration without mocking individual components.

**What's tested:**
- Roubo (theft) claim workflow
- Colisão (collision) claim workflow
- Multi-turn conversations with state persistence
- Plugin execution within workflows
- Document processing and analysis
- Fraud scoring and decision logic
- State transitions across turns

**Files:**
- `tests/e2e/test_complete_workflows.py` — All E2E tests

**Complete roubo workflow:**
```
1. Extract fields from document
   Input: Boletim de Ocorrência with claim details
   Output: Structured claim data (sinistro_tipo, valor, data, etc.)

2. Apply insurance context
   Input: Extracted claim data
   Output: Context rules (SLA, required documents, etc.)

3. Score fraud risk
   Input: Context-enhanced claim data
   Output: Fraud score (0-100)

4. Save state
   Input: Claim state, conversation ID
   Output: Persisted state with TTL in Supabase

5. Trigger workflow
   Input: Claim details
   Output: Workflow event scheduled in Inngest

6. Return decision
   Output: ANÁLISE_PENDENTE status to user
```

**Complete colisão workflow:**
```
Similar to roubo, but with colisão-specific rules:
- Different SLA (20 days vs 10 days)
- Different required documents
- Different fraud risk patterns
```

**Multi-turn conversation:**
```
Turn 1: Initial claim submission → Save state
Turn 2: Request documents → Load state, update, save
Turn 3: Provide fraud analysis → Load state, update, save
Turn 4: Final decision → Load state, finalize
```

**How to run:**
```bash
# Run all E2E tests
pytest tests/e2e/ -v -m e2e

# Run single workflow
pytest tests/e2e/test_complete_workflows.py::test_complete_roubo_workflow -v

# Run with detailed output
pytest tests/e2e/ -v -s
```

**Interpreting results:**
```
test_complete_roubo_workflow PASSED (35s)
test_complete_colisao_workflow PASSED (32s)
test_multi_turn_conversation_workflow PASSED (28s)
test_workflow_with_plugin_execution PASSED (40s)

========== 4 passed in 135.42s ==========
✓ All workflows completed successfully
✓ State persistence working correctly
✓ Plugin execution validated
```

**E2E test expectations:**
- No mocks or stubs
- Real or staging services only
- Complete user journey coverage
- State transitions validated
- Error handling tested
- Timing expectations met

---

## Test Coverage Report

Generate a comprehensive coverage report across all modules:

```bash
# Generate HTML coverage report
pytest tests/ \
  --cov=context_engine \
  --cov=plugins \
  --cov=monitoring \
  --cov=tools \
  --cov-report=html \
  --cov-report=term-missing

# View report
open htmlcov/index.html
```

**Coverage targets:**
- `context_engine/` — > 95% line coverage
- `plugins/` — > 90% line coverage
- `monitoring/` — > 85% line coverage
- `tools/` — > 90% line coverage
- **Overall target** — > 85% coverage

**Coverage report structure:**
```
htmlcov/
├── index.html          # Summary by file
├── status.json         # Machine-readable results
├── context_engine/     # Module breakdown
│   ├── base.html
│   ├── insurance_context.html
│   ├── storage.html
│   └── ...
├── plugins/            # Plugin coverage
├── monitoring/         # Monitoring coverage
└── tools/              # Tool coverage
```

**Interpreting coverage:**
- **Line coverage** — Percentage of lines executed
- **Branch coverage** — Percentage of if/else paths taken
- **Missing** — Lines not covered by tests

Example:
```
Name                          Stmts   Miss  Cover   Missing
────────────────────────────────────────────────────────────
context_engine/__init__.py        2      0   100%
context_engine/base.py          145      5    97%   123, 156-160, 234
context_engine/insurance...     234      8    97%   45, 89, 201-205, 312
context_engine/storage.py       189      6    97%   78, 145, 267-271, 334
────────────────────────────────────────────────────────────
TOTAL                          1200     35    97%
```

---

## Continuous Integration

All tests should run automatically in CI/CD pipeline:

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov locust
      
      - name: Run unit tests
        run: pytest tests/unit/ -v
      
      - name: Run integration tests (staging)
        if: github.event_name == 'push'
        env:
          SUPABASE_STAGING_URL: ${{ secrets.SUPABASE_STAGING_URL }}
          SUPABASE_STAGING_KEY: ${{ secrets.SUPABASE_STAGING_KEY }}
          INNGEST_STAGING_KEY: ${{ secrets.INNGEST_STAGING_KEY }}
        run: pytest tests/integration/ -v
      
      - name: Run performance tests
        run: pytest tests/performance/ -v -m performance
      
      - name: Run security tests
        run: pytest tests/security/ -v -m security
      
      - name: Run chaos tests
        run: pytest tests/chaos/ -v -m chaos
      
      - name: Generate coverage report
        run: |
          pytest tests/ \
            --cov=context_engine \
            --cov=plugins \
            --cov=monitoring \
            --cov-report=html \
            --cov-report=term
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
```

### Test Execution Timeline

```
Phase 1: Unit Tests (5 min)
├── Phase 1-3 components
└── Fast, no external services

Phase 2: Integration Tests (10 min)
├── Supabase staging
├── Inngest staging
└── Requires credentials

Phase 3: Performance Tests (5 min)
├── Latency benchmarks
├── Throughput measurement
└── Baseline comparison

Phase 4: Security Tests (2 min)
├── Vulnerability checks
├── Input validation
└── Fast, no external services

Phase 5: Chaos Tests (8 min)
├── Failure scenarios
├── Memory leak detection
└── Includes load simulation

Total estimated: 30 minutes
```

---

## Troubleshooting

### Staging credentials not set

**Problem:** Integration tests skipped with "SUPABASE_STAGING_URL not set"

**Solution:**
```bash
# Set environment variables
export SUPABASE_STAGING_URL="https://your-staging.supabase.co"
export SUPABASE_STAGING_KEY="eyJhbGc..."
export INNGEST_STAGING_KEY="inngest_..."

# Or create .env file
echo "SUPABASE_STAGING_URL=..." >> .env
echo "SUPABASE_STAGING_KEY=..." >> .env
echo "INNGEST_STAGING_KEY=..." >> .env

# Run with python-dotenv
pytest tests/integration/ -v
```

### Performance targets not met

**Problem:** Performance test fails: "avg_ms (150.5) > target (100)"

**Solution:**
1. Check system load: `top`, `htop`, Activity Monitor
2. Close other applications
3. Run on isolated machine
4. Run test multiple times: `pytest tests/performance/ -v --count=3`
5. Profile slow operations: Use `cProfile` or `py-spy`
6. Check network latency for Supabase tests
7. Verify Python version (3.11+)
8. Check for disk/network constraints

### Import errors in tests

**Problem:** `ModuleNotFoundError: No module named 'context_engine'`

**Solution:**
```bash
# Ensure you're in project root
cd ~/Projects/88i-sinistro-harness

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run pytest from project root
pytest tests/ -v
```

### Database cleanup issues

**Problem:** Staging database has test data from failed runs

**Solution:**
```bash
# Manual cleanup (danger: deletes all test records)
# From Python:
from supabase import create_client
client = create_client(url, key)
client.table("context_cache").delete().eq("test", True).execute()

# Or use Supabase dashboard to browse and delete
```

### Test timeout issues

**Problem:** Integration tests hang or timeout

**Solution:**
```bash
# Run with shorter timeout
pytest tests/integration/ -v --timeout=30

# Or increase timeout if network is slow
pytest tests/integration/ -v --timeout=60
```

### Locust cannot connect to server

**Problem:** "Error: Connection refused to http://localhost:8000"

**Solution:**
```bash
# Verify server is running
ps aux | grep uvicorn

# Start server if not running
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Verify server is responsive
curl http://localhost:8000/health

# Try different port if 8000 in use
locust -f tests/load/locustfile.py --host=http://localhost:8001
```

### Memory leak detection false positives

**Problem:** Memory leak test fails with "memory_increase > 50MB"

**Solution:**
```bash
# Run test in isolation (other tests can affect memory)
pytest tests/chaos/test_failure_scenarios.py::test_memory_leak_under_load -v

# Run with garbage collection
python -m pytest tests/chaos/ -v --gc=collect

# Check system memory before test
free -h
```

---

## Performance Targets Summary

### Operation Latency

All operations should complete within max average latency:

```
Extract Fields:      100 ms (10 ops/sec)
Fraud Scoring:       150 ms (6 ops/sec)
Context Injection:   50 ms (20 ops/sec)
Plugin Load:         200 ms (5 ops/sec)
State Persistence:   300 ms (3 ops/sec)
Monitoring Trace:    10 ms (100 ops/sec)
```

### System Throughput

```
Concurrent Users:    100+
Total Throughput:    > 100 req/sec
Error Rate:          < 0.1%
Response Time p95:   < 500ms
Response Time p99:   < 1000ms
```

### Resource Usage

```
Memory/Operation:    < 50MB for 1000 ops
CPU Usage:           < 80% sustained
Database Connections: < 20 pool max
```

---

## Security Checklist

Before deploying Phase 4, verify all security checks:

- ✅ SQL injection prevention (parameterized queries)
- ✅ Authentication required (no anonymous access)
- ✅ Input validation (type checking, bounds)
- ✅ Secrets not in logs (redact API keys)
- ✅ Plugin isolation (no escape vectors)
- ✅ Rate limiting (async concurrency)
- ✅ CORS headers (secure origin check)
- ✅ Data validation (enum types, ranges)
- ✅ Error messages (no sensitive info)
- ✅ Crypto hashing (passwords, tokens)
- ✅ Session management (TTL, revocation)
- ✅ Dependency scanning (no known CVEs)

Run security tests before every deployment:
```bash
pytest tests/security/ -v -m security
```

---

## Next Steps

### Phase 4 Complete ✅

With comprehensive testing in place, the system is ready for:

1. **Production Deployment** — All tests passing with high coverage
2. **Monitoring** — Langfuse integration tracks real usage
3. **Performance Optimization** — Baseline established for improvements
4. **Security Hardening** — Vulnerabilities identified and fixed
5. **Load Capacity** — Concurrent user limits determined

### Phase 5: Deployment & Monitoring

Next phase focuses on:

- **Docker containerization** — Package system for deployment
- **CI/CD pipeline** — Automated testing on every commit
- **Health checks** — Startup validation and readiness probes
- **Monitoring dashboard** — Real-time metrics and alerts
- **Log aggregation** — Centralized error tracking
- **Backup strategy** — Data recovery procedures

### Continuous Improvement

After Phase 4, establish practices:

- **Daily test runs** — Automated via CI/CD (GitHub Actions)
- **Weekly reviews** — Performance trend analysis
- **Monthly audits** — Security and compliance checks
- **Quarterly planning** — Capacity planning and scaling

---

## Resources

### Documentation
- **[tests/README.md](../tests/README.md)** — Test suite overview
- **[PLUGIN_DEVELOPMENT_GUIDE.md](./PLUGIN_DEVELOPMENT_GUIDE.md)** — Plugin system
- **[TOOLS_DOCUMENTATION.md](./TOOLS_DOCUMENTATION.md)** — Tool reference

### Test Files
- Integration: `tests/integration/`
- Performance: `tests/performance/`
- Security: `tests/security/`
- Chaos: `tests/chaos/`
- Load: `tests/load/`
- E2E: `tests/e2e/`

### External References
- **[pytest docs](https://docs.pytest.org/)** — Test framework
- **[pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)** — Async testing
- **[Locust docs](https://docs.locust.io/)** — Load testing
- **[Supabase docs](https://supabase.com/docs)** — Database
- **[Inngest docs](https://www.inngest.com/docs)** — Workflows
- **[Langfuse docs](https://langfuse.com/docs)** — Observability

---

**Phase 4 Testing Guide v1.0**  
Created: May 27, 2026  
Last Updated: May 27, 2026  
Status: ✅ Complete
