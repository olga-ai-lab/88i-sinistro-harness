# 88i Sinistro API - Incident Runbooks

Operational runbooks for common incident scenarios in the 88i Sinistro API production environment.

## Incident Severity Levels

### P1 - Critical
- **Impact**: Service completely unavailable or major data loss occurring
- **SLA**: Acknowledgment within 5 minutes, updates every 15 minutes
- **Escalation**: Immediate page to on-call engineers and team leads
- **Examples**: Complete API outage, database down, data corruption, security breach
- **Target Resolution**: 30 minutes

### P2 - High
- **Impact**: Service significantly degraded, major functionality impaired
- **SLA**: Acknowledgment within 15 minutes, updates every 30 minutes
- **Escalation**: Page to on-call senior engineer and notify team lead
- **Examples**: >5% error rate, >300ms P95 latency, partial service degradation
- **Target Resolution**: 1 hour

### P3 - Medium
- **Impact**: Service degraded but usable, minor functionality affected
- **SLA**: Acknowledgment within 30 minutes, updates every hour
- **Escalation**: Notify team lead and create incident ticket
- **Examples**: Intermittent errors <5%, elevated latency, non-critical feature degradation
- **Target Resolution**: 4 hours

### P4 - Low
- **Impact**: Minimal user impact, informational issues
- **SLA**: Acknowledgment within business day
- **Escalation**: Create ticket and document
- **Examples**: Log warnings, deprecation notices, non-critical alerts
- **Target Resolution**: Best effort

---

## Common Incident Scenarios

### Scenario 1: High Error Rate (>5%)

**Detection Signal**: Error rate exceeds 5% of requests for >2 consecutive minutes

**Severity**: P2 High

#### Initial Assessment (0-5 min)

1. Confirm the alert by checking the dashboard:
   ```bash
   curl https://metrics.88i-sinistro.io/api/error_rate?window=5m
   ```

2. Check which endpoints are failing:
   ```bash
   curl https://metrics.88i-sinistro.io/api/errors?group_by=endpoint&window=5m | jq .
   ```

3. Identify the error types:
   ```bash
   curl https://metrics.88i-sinistro.io/api/errors?group_by=error_type&window=5m | jq .
   ```

#### Investigation Steps

1. Check application logs for errors:
   ```bash
   kubectl logs -n production -l app=sinistro-api --since=10m --all-containers=true | grep ERROR
   ```

2. Examine error patterns by checking recent deployments:
   ```bash
   kubectl rollout history deployment/sinistro-api -n production --max=5
   kubectl describe deployment sinistro-api -n production | grep "Image:"
   ```

3. Check database connectivity:
   ```bash
   curl http://localhost:9090/health/database
   ```

4. Monitor system resources:
   ```bash
   kubectl top nodes
   kubectl top pods -n production -l app=sinistro-api
   ```

5. Check external service dependencies:
   ```bash
   curl https://metrics.88i-sinistro.io/api/dependency_health
   ```

#### Common Causes & Resolution

**Recent Deployment**:
- Trigger automatic rollback if error rate >10% for >1 min:
  ```bash
  kubectl rollout undo deployment/sinistro-api -n production
  kubectl rollout status deployment/sinistro-api -n production
  ```
- Monitor metrics post-rollback for 5 minutes

**Code Issue**:
- If error type is application-level (NullPointerException, ValidationError):
  - Review recent code changes for the affected endpoint
  - Check feature flags to disable problematic features:
    ```bash
    kubectl set env deployment/sinistro-api -n production FEATURE_X_ENABLED=false
    ```

**Database Issues**:
- Restart database connections pool:
  ```bash
  kubectl exec -it sinistro-api-pod -n production -- python -c "from app.db import restart_pool; restart_pool()"
  ```

**Rate Limiting / DDoS**:
- Check request patterns:
  ```bash
  curl https://metrics.88i-sinistro.io/api/requests?group_by=source_ip&window=5m | head -20
  ```
- Activate rate limiting if needed:
  ```bash
  kubectl set env deployment/sinistro-api -n production RATE_LIMIT_ENABLED=true
  ```

#### Escalation

- P2 escalation after 15 minutes of >5% error rate
- Contact on-call engineer and team lead
- Create incident ticket with error_rate and error_type details

---

### Scenario 2: High Latency (>300ms P95)

**Detection Signal**: P95 latency exceeds 300ms for >3 consecutive minutes

**Severity**: P2 High

#### Initial Assessment (0-5 min)

1. Confirm latency spike:
   ```bash
   curl https://metrics.88i-sinistro.io/api/latency?percentile=p95&window=5m
   ```

2. Identify affected endpoints:
   ```bash
   curl https://metrics.88i-sinistro.io/api/latency?group_by=endpoint&percentile=p95&window=5m | jq .
   ```

3. Check latency distribution:
   ```bash
   curl https://metrics.88i-sinistro.io/api/latency?group_by=operation&window=5m | jq .
   ```

#### Resource Check & Analysis

1. Check CPU usage:
   ```bash
   kubectl top nodes
   kubectl top pods -n production -l app=sinistro-api --sort-by=cpu
   ```

2. Check memory usage:
   ```bash
   kubectl top pods -n production -l app=sinistro-api --sort-by=memory
   ```

3. Check disk I/O:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- iostat -x 1 5
   ```

4. Check database query performance:
   ```bash
   # Connect to database and check slow logs
   kubectl exec -it postgres-pod -n production -- \
     psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

5. Monitor network throughput:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- \
     iftop -n -s 5 (if available) or use: ss -in
   ```

#### Scaling Actions

1. **Horizontal Scaling** - Increase pod replicas:
   ```bash
   kubectl scale deployment sinistro-api -n production --replicas=10
   kubectl rollout status deployment/sinistro-api -n production --timeout=5m
   ```

2. **Vertical Scaling** - Increase resource limits (requires deployment edit):
   ```bash
   kubectl set resources deployment sinistro-api -n production \
     --requests=cpu=2,memory=2Gi --limits=cpu=4,memory=4Gi
   ```

3. **Cache Optimization** - Check cache hit rates:
   ```bash
   curl https://metrics.88i-sinistro.io/api/cache_stats?window=5m
   ```

4. **Query Optimization** - If database is bottleneck:
   ```bash
   # Add index on frequently queried columns
   kubectl exec -it postgres-pod -n production -- \
     psql -c "CREATE INDEX CONCURRENTLY idx_field ON table(field);"
   ```

#### Escalation

- P2 escalation after 10 minutes of >300ms P95 latency
- Contact on-call engineer
- Initiate horizontal scaling if not already done

---

### Scenario 3: Database Connection Failures

**Detection Signal**: Database connection errors or connection pool exhaustion

**Severity**: P1 Critical (if affecting all requests) / P2 High (if partial)

#### Initial Assessment (0-5 min)

1. Check database connectivity:
   ```bash
   curl http://localhost:9090/health/database
   ```

2. Verify database is running:
   ```bash
   kubectl get pods -n production -l app=postgres
   kubectl logs -n production postgres-0 --tail=50
   ```

3. Check network connectivity to database:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- \
     nc -zv postgres.default.svc.cluster.local 5432
   ```

#### Pool Status Check

1. Check connection pool status:
   ```bash
   curl http://localhost:9090/metrics/connection_pool
   ```
   Expected response includes:
   - `active_connections`: Currently in use
   - `idle_connections`: Available for use
   - `waiting_requests`: Requests waiting for a connection
   - `max_connections`: Maximum pool size

2. Monitor pool exhaustion:
   ```bash
   kubectl logs -n production -l app=sinistro-api --since=5m | grep "connection pool"
   ```

3. Check for long-running queries holding connections:
   ```bash
   kubectl exec -it postgres-pod -n production -- \
     psql -c "SELECT pid, duration, query FROM pg_stat_activity WHERE state != 'idle';"
   ```

#### Idle Connection Cleanup

1. View idle connections (open for >30 min):
   ```bash
   kubectl exec -it postgres-pod -n production -- \
     psql -c "SELECT pid, usename, state, state_change FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '30 min';"
   ```

2. Terminate idle connections:
   ```bash
   kubectl exec -it postgres-pod -n production -- \
     psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < now() - interval '30 min';"
   ```

3. Restart database connection pool in application:
   ```bash
   kubectl set env deployment/sinistro-api -n production \
     POOL_RESET_REQUIRED=true
   kubectl rollout restart deployment/sinistro-api -n production
   ```

#### Resolution Steps

1. **If database is down**: 
   - Check database pod status and restart if needed:
     ```bash
     kubectl rollout restart statefulset/postgres -n production
     ```
   - Restore from backup if data is corrupt:
     ```bash
     kubectl exec -it postgres-pod -n production -- \
       pg_restore -d sinistro /backups/latest.dump
     ```

2. **If connections leak**:
   - Identify applications leaking connections:
     ```bash
     kubectl top pods -n production | grep memory
     ```
   - Restart affected deployment:
     ```bash
     kubectl rollout restart deployment/sinistro-api -n production
     ```

3. **If network issue**:
   - Check pod-to-pod connectivity:
     ```bash
     kubectl run -it --image=busybox debug --restart=Never -- \
       sh -c 'nc -zv postgres.default.svc.cluster.local 5432'
     ```

#### Escalation

- P1 escalation immediately (critical if 100% failure rate)
- P2 escalation after 5 minutes of failures
- Page on-call DBA and team lead

---

### Scenario 4: Memory Leak

**Detection Signal**: Memory usage increasing >5%/hour without corresponding load increase

**Severity**: P3 Medium (becomes P2 if approaching OOM)

#### Initial Assessment (0-10 min)

1. Confirm memory leak by checking memory trend:
   ```bash
   # Get current memory usage
   kubectl top pods -n production -l app=sinistro-api
   
   # Check memory over time (requires metrics)
   curl https://metrics.88i-sinistro.io/api/memory_usage?window=1h | jq .
   ```

2. Calculate growth rate:
   ```bash
   # Example: 500MB at T0, 530MB at T10 = 3% per 10 min = 30% per 100 min
   echo "Growth rate: (current - initial) / initial / hours_elapsed * 100"
   ```

3. Estimate time to OOM:
   ```bash
   # POD_LIMIT (usually 2Gi = 2048MB)
   # current_usage, memory_growth_rate_per_hour
   echo "Time to OOM: (POD_LIMIT - current_usage) / memory_growth_rate_per_hour"
   ```

#### Memory Monitoring

1. Enable detailed memory metrics:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- \
     python -c "import tracemalloc; tracemalloc.start()"
   ```

2. Monitor memory by component:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- \
     python -c "import gc; gc.collect(); import os; os.system('ps aux | grep python')"
   ```

3. Check for high object counts:
   ```bash
   kubectl logs -n production -l app=sinistro-api --since=1h | grep "object count"
   ```

#### Profiling & Debugging

1. Generate memory profile:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- \
     python -m memory_profiler --include-children app/main.py
   ```

2. Use py-spy for CPU & memory profiling:
   ```bash
   # Install py-spy in container if needed
   kubectl exec -it sinistro-api-pod -n production -- \
     pip install py-spy
   
   # Profile for 60 seconds (requires --privileged or CAP_SYS_PTRACE)
   kubectl exec -it sinistro-api-pod -n production -- \
     py-spy record -o /tmp/profile.svg --duration=60 -- python -m app.main
   ```

3. Check for circular references:
   ```bash
   kubectl exec -it sinistro-api-pod -n production -- \
     python -c "
       import gc
       gc.collect()
       objects = gc.get_objects()
       print(f'Total objects: {len(objects)}')
       from collections import Counter
       types = Counter(type(obj).__name__ for obj in objects)
       for t, count in types.most_common(10):
           print(f'{t}: {count}')
     "
   ```

4. Check cache sizes:
   ```bash
   curl http://localhost:9090/metrics/caches
   ```

#### Resolution Steps

1. **Identify leak source**:
   - Check application logs for unbounded cache growth:
     ```bash
     kubectl logs -n production -l app=sinistro-api --since=1h | grep -i cache
     ```
   - Review recent code changes that add caching

2. **Quick fixes**:
   - Clear caches:
     ```bash
     curl -X POST http://localhost:9090/admin/clear_caches
     ```
   - Reduce cache TTL:
     ```bash
     kubectl set env deployment/sinistro-api -n production \
       CACHE_TTL_SECONDS=300
     ```
   - Disable problematic cache:
     ```bash
     kubectl set env deployment/sinistro-api -n production \
       FEATURE_X_CACHE_ENABLED=false
     ```

3. **Restart if urgent**:
   - Rolling restart to prevent OOM kill:
     ```bash
     kubectl rollout restart deployment/sinistro-api -n production
     ```

4. **Long-term fix**:
   - Deploy code fix that properly cleans up resources
   - Add memory limit enforcement: `kubectl set resources deployment/sinistro-api -n production --limits memory=2Gi`
   - Add memory monitoring and alerting for future detection

#### Escalation

- P3 escalation after 1 hour of confirmed growth
- P2 escalation if time to OOM <30 minutes
- Contact on-call engineer and notify platform team

---

## Escalation Procedures

| Issue Type | Detection Threshold | Time to P2 | Time to P1 | Owner | Escalate To |
|------------|-------------------|-----------|-----------|-------|-------------|
| Error Rate | >5% for 2 min | 15 min | 30 min | On-call Eng | Tech Lead |
| Latency P95 | >300ms for 3 min | 10 min | 20 min | On-call Eng | Senior Eng |
| DB Failures | >10 errors/min | 5 min | 10 min | On-call DBA | DBA Lead |
| Memory Leak | >5%/hour growth | 60 min | 30 min (if OOM <30min) | On-call Eng | Platform Lead |
| Disk Space | >85% used | 30 min | 15 min (if >95%) | Ops | Ops Lead |
| CPU | >80% for 5 min | 20 min | 10 min | On-call Eng | Senior Eng |
| Network | Packet loss >1% | 15 min | 10 min | Ops | Network Lead |
| Security | Breach detected | Immediate | N/A | Security | CISO |

---

## Runbook Usage

1. **Stay Calm**: Follow the runbook step-by-step
2. **Parallel Investigation**: Start monitoring while investigating root cause
3. **Communicate**: Update status page and notify stakeholders every 15-30 minutes
4. **Document**: Log all commands executed and findings for post-mortem
5. **Escalate Early**: Don't wait for the escalation timer—escalate if unsure
6. **Post-Incident**: Create follow-up ticket to prevent recurrence

---

## Quick Reference Commands

```bash
# Health checks
curl http://localhost:9090/health
curl http://localhost:9090/health/database
curl http://localhost:9090/health/services

# Metrics
curl https://metrics.88i-sinistro.io/api/error_rate?window=5m
curl https://metrics.88i-sinistro.io/api/latency?percentile=p95&window=5m
curl https://metrics.88i-sinistro.io/api/memory_usage?window=1h

# Kubernetes
kubectl get pods -n production
kubectl logs -n production -l app=sinistro-api --since=10m
kubectl top nodes
kubectl top pods -n production

# Database
kubectl exec -it postgres-pod -n production -- psql -d sinistro
```

---

## Contact Information

- **On-Call Engineer**: `+1-XXX-XXX-XXXX` (PagerDuty)
- **Team Slack**: #88i-sinistro-incident
- **Status Page**: https://status.88i-sinistro.io
- **War Room**: https://zoom.us/j/INCIDENT_ZOOM_ID (activate during P1)
