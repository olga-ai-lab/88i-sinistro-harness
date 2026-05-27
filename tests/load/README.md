# Load Testing

Load tests using Locust framework.

## Installation

```bash
pip install locust
```

## Running Load Tests

```bash
# Start the agent server first
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# In another terminal, run Locust
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Or run with specific users and spawn rate
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m
```

## Web UI

Default: http://localhost:8089

## Metrics to Monitor

- Response time (p50, p95, p99)
- Requests/sec
- Failures
- Error rates

## Performance Targets

- Extract fields: < 500ms response
- Score fraud: < 750ms response
- Save state: < 1s response
- Inject context: < 200ms response
- System throughput: > 100 req/sec
