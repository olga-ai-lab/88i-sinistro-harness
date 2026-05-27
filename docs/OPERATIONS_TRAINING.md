# Operations Team Training Agenda

**Program Name:** 88i Sinistro Agent Operations Training Program  
**Version:** 1.0  
**Last Updated:** May 27, 2026  
**Training Duration:** 3.5 hours (3 sessions)  
**Target Audience:** Operations engineers, on-call rotation, incident responders  
**Certification Required:** Yes, before on-call rotation eligibility

---

## Executive Summary

This training program prepares operations engineers to manage the 88i Sinistro Agent in production. The program covers system architecture, monitoring and observability, incident response procedures, and operational procedures. Participants must complete all three sessions and pass a competency assessment before joining the on-call rotation.

**Training Schedule:**
- Session 1: System Overview & Monitoring (1 hour)
- Session 2: Incident Response & Runbooks (1.5 hours)
- Session 3: Operational Procedures (1 hour)
- Assessment & Certification: 30 minutes

---

## Session 1: System Overview & Monitoring (1 hour)

### Objectives
By the end of this session, participants will be able to:
- Understand the 88i Sinistro Agent architecture and deployment model
- Navigate and interpret Prometheus metrics
- Understand Grafana dashboard structure and alerting
- Identify key performance indicators (KPIs) and SLA targets
- Perform basic monitoring health checks

### Topics

#### Topic 1: System Architecture (15 minutes)

**Content:**
- FastAPI application stack running on Railway.app
- Microservice components:
  - Extract Service: Document text extraction (SLA: <100ms P95)
  - Fraud Detection Service: Claims fraud analysis (SLA: <150ms P95)
  - Database Layer: Supabase PostgreSQL for persistence
  - Cache Layer: Redis for session state (optional)
  - Message Queue: Inngest for async processing
- External integrations:
  - Anthropic API (Claude 3) for AI inference
  - Langfuse for LLM observability
  - Inngest for workflow orchestration
  - PagerDuty for alerting
- Deployment model:
  - Railway.app environment with auto-scaling
  - Zero-downtime deployments
  - Automatic health checks and recovery
  - Geographic redundancy considerations

**Key Diagram References:**
- Architecture diagram (see `docs/arquitetura.md`)
- Technology stack (see `TOOLS_DOCUMENTATION.md`)
- Deployment pipeline (see `PHASE5_DEPLOYMENT_GUIDE.md`)

**Handout Materials:**
- System architecture diagram
- Technology stack reference sheet
- External integration endpoints and credentials management

#### Topic 2: Monitoring Setup (20 minutes)

**Content:**

**Prometheus Configuration:**
- Scrape jobs configuration:
  - `job_name: "88i-sinistro-app"` - Application metrics (port 8000/metrics)
  - `job_name: "prometheus"` - Prometheus self-metrics
  - `scrape_interval: 15s` - Metric collection frequency
- Metric types:
  - Counter: Total request count, total errors
  - Gauge: Current memory usage, active connections
  - Histogram: Request latency distribution, response sizes
  - Summary: Request duration percentiles
- Common Prometheus queries:
  ```
  rate(requests_total[5m])                    # Request rate
  histogram_quantile(0.95, request_duration)  # P95 latency
  rate(errors_total[5m]) / rate(requests_total[5m])  # Error rate
  process_resident_memory_bytes / 1024 / 1024  # Memory in MB
  ```

**Grafana Dashboards:**
- Main dashboard: Overview with 4 panels
  - Request rate (green: healthy)
  - Error rate (red: problem indicator)
  - Latency percentiles (P50, P95, P99)
  - Resource utilization (CPU, memory)
- Service-specific dashboards:
  - Extract Service dashboard
  - Fraud Detection Service dashboard
  - Database performance dashboard
  - Cache hit ratio dashboard
- Alert dashboard:
  - Current active alerts
  - Alert history (last 24 hours)
  - Alert status (firing, resolved)

**Alert Rules and Thresholds:**
- P1 (Critical) Alerts:
  - Error rate > 5% for 5 minutes → Immediate escalation
  - Service unavailable (HTTP 503) → Page on-call
  - Database connection pool exhausted → Critical
  - Memory usage > 90% → Immediate action
- P2 (Warning) Alerts:
  - Error rate > 1% for 15 minutes → Investigate
  - P95 latency > 200ms for 10 minutes → Monitor
  - CPU usage > 80% for 10 minutes → Review
  - High request queue depth → Scaling check
- P3 (Info) Alerts:
  - Deployment completed successfully
  - Backup job completed
  - Cache eviction high
  - Slow query detected (>1000ms)

**PagerDuty Integration:**
- P1 alerts automatically trigger PagerDuty page
- Secondary on-call receives notification after 5 minutes if primary doesn't ack
- Escalation to manager after 15 minutes
- Integration setup and webhook verification

**Handout Materials:**
- Prometheus query cheat sheet
- Grafana dashboard access instructions
- Alert threshold configuration reference
- PagerDuty integration guide

#### Topic 3: Key Metrics and SLA Targets (15 minutes)

**Content:**

**Application Metrics:**

| Metric | Current Target | P95 Target | Warning Threshold | Critical Threshold |
|--------|----------------|------------|-------------------|-------------------|
| Request Rate | 100 req/min | N/A | >500 req/min | >1000 req/min |
| Error Rate | <1% | N/A | >1% | >5% |
| P95 Latency (Extract) | <100ms | <150ms | >150ms | >300ms |
| P95 Latency (Fraud) | <150ms | <200ms | >250ms | >500ms |
| P99 Latency | N/A | <300ms | >400ms | >600ms |
| Memory Usage | <500MB | N/A | >700MB | >900MB |
| CPU Usage | <30% | N/A | >60% | >80% |
| Database Connections | 5-10 | N/A | >20 | >30 |
| Cache Hit Ratio | >80% | N/A | <60% | <40% |

**Business Metrics:**
- Availability: 99.9% uptime SLA (8.6 hours downtime per month max)
- Response time: Extract <100ms P95, Fraud <150ms P95
- Error budget: 99.9% = 43 minutes of errors per month
- Deployment frequency: Up to 5 per day
- Mean Time To Recovery (MTTR): <15 minutes for P1, <30 minutes for P2

**Derived Metrics (calculated from raw metrics):**
- Service health score (0-100): Composite of uptime, latency, error rate
- Apdex score: Application Performance Index (satisfied/tolerated/frustrated)
- Cost per transaction: USD/processed claim (optimization target)

**Handout Materials:**
- SLA target card
- Key metrics reference sheet
- Metrics glossary and formulas

#### Topic 4: Dashboard Walkthrough (10 minutes)

**Live Demo:**
- Access Grafana dashboard (credentials provided)
- Navigate to "88i Sinistro Main" dashboard
- Point out the four main panels:
  - Request rate graph (last 24 hours, auto-refresh every 30s)
  - Error rate graph (red line = problems)
  - Latency graph (P50, P95, P99 lines)
  - Resource utilization graph (CPU%, Memory%)
- Show alert history tab
- Demonstrate Prometheus query builder
  - Search for metric name
  - Apply rate() and time range functions
  - Export to dashboard
- Show how to set custom time ranges
- Demonstrate drill-down to service-specific dashboards
- Show how to set alert thresholds

**Hands-On Activity (5 minutes):**
- Each participant queries one metric in Prometheus
- Screenshot their result
- Verify understanding of results

**Handout Materials:**
- Dashboard access URL and credentials
- Screenshot of main dashboard with annotations
- Prometheus query reference guide

### Materials Provided

- [ ] Architecture diagram (PDF)
- [ ] System stack reference sheet
- [ ] Prometheus query cheat sheet (printed)
- [ ] Grafana dashboard guide (PDF)
- [ ] SLA target reference card
- [ ] Key metrics glossary
- [ ] Sample dashboard screenshots with annotations

### Assessment (Session 1)

**Knowledge Check Questions:**
1. What is the P95 latency target for the Extract service?
2. How often are Prometheus metrics scraped?
3. What is the PagerDuty integration threshold for P1 alerts?
4. Name three external integrations in the system.
5. What is the uptime SLA target?

**Hands-On Task:**
- Query the request rate metric in Prometheus
- Interpret the result and explain what it means
- Navigate to the Fraud Detection dashboard in Grafana

---

## Session 2: Incident Response & Runbooks (1.5 hours)

### Objectives
By the end of this session, participants will be able to:
- Execute the 6-phase incident response framework
- Follow and adapt runbooks for common incidents
- Use logs and metrics to diagnose issues
- Know when to escalate vs. resolve independently
- Communicate effectively during incidents
- Conduct practice incident simulations

### Topics

#### Topic 1: 6-Phase Incident Response Framework (20 minutes)

**Content:**

The incident response process is structured in six phases to ensure systematic, documented handling of production issues.

**Phase 1: Detection & Alerting (Duration: 0-5 minutes)**
- Alert triggered in Prometheus or manually reported
- Alert severity determined (P1/P2/P3)
- PagerDuty page sent to on-call engineer
- Slack notification in #operations channel
- Initial context: Alert name, threshold, affected service
- **Actions:**
  - Ack the PagerDuty alert within 5 minutes
  - Check Grafana dashboard for context
  - Post initial response in Slack thread
  - Determine if escalation needed
- **Owner:** On-call engineer

**Phase 2: Initial Investigation & Triage (Duration: 5-15 minutes)**
- Review related metrics (not just the alert metric)
- Check application logs for error patterns
- Verify if issue is widespread or localized
- Determine if issue is in app, database, or external service
- Estimate impact (number of users/requests affected)
- **Actions:**
  - Run diagnostic queries in Prometheus
  - Tail application logs (last 5-10 minutes)
  - Check recent deployments
  - Verify all dependencies are healthy
  - Update incident severity if needed
  - Post findings in Slack with screenshots
- **Owner:** On-call engineer + secondary (if P1)
- **Runbook Link:** Jump to appropriate runbook based on symptoms

**Phase 3: Communication & Escalation (Duration: Ongoing)**
- Notify stakeholders based on severity
  - P1: Manager, product lead, customer success
  - P2: Team lead, product lead
  - P3: Team lead (async)
- Update status channel every 5 minutes (P1) or 15 minutes (P2)
- Use status page (if public incident)
- Escalate to secondary/manager if needed
- **Actions:**
  - Post incident summary to #operations-incidents
  - Tag appropriate people
  - Use incident template (see below)
  - Update every 5 minutes
- **Template:**
  ```
  🚨 INCIDENT: [Service] - [Brief Description]
  Severity: P1 | Start: [TIME] UTC
  Status: INVESTIGATING
  Affected: [Users/Feature]
  Impact: [# requests/users]
  Owner: [@on-call]
  Next update: [TIME+5min]
  ```
- **Owner:** On-call engineer (communication)

**Phase 4: Remediation & Implementation (Duration: 15-45 minutes)**
- Determine root cause from investigation
- Decide on fix strategy:
  - Rollback previous deployment
  - Deploy hotfix
  - Scale up resources
  - Adjust configuration
  - Failover to backup
- Execute chosen remediation from runbook
- Monitor metrics closely during execution
- **Actions:**
  - Run remediation commands carefully
  - Watch for immediate effect on metrics
  - Have rollback plan ready
  - Document exact commands run
  - Post each action in Slack
- **Owner:** On-call engineer (+ senior if complex)

**Phase 5: Verification & Stability (Duration: 45-60 minutes)**
- Verify metrics return to normal
  - Error rate back to <1%
  - Latency back to baseline
  - Resource usage stabilized
- Run synthetic tests to confirm functionality
- Wait 5-10 minutes to ensure stability
- Gradually scale back any temporary increases
- **Actions:**
  - Run health check endpoint
  - Execute critical path test (extract + fraud)
  - Monitor for 10 minutes
  - Check for secondary issues
  - Update Slack with resolution time
- **Owner:** On-call engineer + secondary verification

**Phase 6: Post-Incident Activities (Duration: T+24 hours)**
- Create incident post-mortem
- Document root cause and fix
- Identify preventive measures
- Update runbooks if needed
- Create action items for prevention
- Close incident in tracking system
- **Actions:**
  - Write post-mortem (template in Session 3)
  - Schedule 30-min sync with team
  - Update relevant runbooks
  - Create Jira tickets for prevention
  - Set reminder for action item follow-up
  - Share learnings in #incident-learnings
- **Owner:** On-call engineer + team

**Escalation Matrix:**
```
Level 1: On-Call Engineer
- P3 issues, routine operations
- Authority: Execute runbooks, restart services
- Time limit: 30 minutes to resolve or escalate

Level 2: Secondary + Engineering Team Lead
- P2 issues, code-level debugging needed
- Authority: Deploy hotfixes, temporary config changes
- Time limit: 15 minutes to resolve or escalate

Level 3: Engineering Manager + Product Lead
- P1 issues, major system failures
- Authority: Approve rollbacks, emergency decisions
- Escalation: Customer notification, executive updates

Level 4: Director + Customer Success (Customer-facing P1)
- Highest priority
- Authority: All decisions, customer communication
- Actions: Executive status calls, compensation decisions
```

**Communication Templates:**

*Initial Response (first 5 min):*
```
👀 INVESTIGATING: [Service] - [Issue detected]
Will update in 5 minutes. Thanks for your patience.
```

*Ongoing Updates (every 5 min):*
```
📊 Status Update (T+[TIME])
Investigation: [Key finding]
Current Impact: [Affected metric]
Next Step: [What we're doing]
ETA: [Time estimate]
```

*Resolution:*
```
✅ RESOLVED (T+[MINUTES])
Root Cause: [What was wrong]
Fix Applied: [What we did]
Impact: [Users affected: #]
Post-Mortem: Will schedule within 24 hours
```

**Handout Materials:**
- 6-Phase framework flowchart (laminated)
- Incident template for Slack (copy/paste)
- Escalation matrix contact card
- Communication templates (printed)

#### Topic 2: Runbook Walkthroughs (40 minutes)

**Runbook 1: High Error Rate Incident (10 minutes)**

**Trigger:** Error rate > 5% for 5 minutes

**Expected Duration:** 5-15 minutes to resolve

**Step-by-Step:**

1. **Verify Alert** (1 min)
   - Check Prometheus alert details
   - Confirm error rate from dashboard
   - Note the time period and exact percentage

2. **Collect Context** (2 min)
   - Query error distribution by endpoint
     ```
     topk(5, rate(errors_total{job="88i-app"}[5m]))
     ```
   - Check which service has highest errors
     - Extract service errors
     - Fraud detection errors
   - Look at status codes: 500 (server error) vs 4xx (client error)

3. **Check Application Logs** (2 min)
   - Tail logs for last 10 minutes
     ```
     tail -f /var/log/88i-sinistro/app.log | grep ERROR | tail -20
     ```
   - Look for recurring error messages
   - Check for stack traces
   - Note any service-specific errors

4. **Check Dependencies** (2 min)
   - Verify Anthropic API is healthy (external status page)
   - Check Supabase database status
   - Verify Redis connection if applicable
   - Check Inngest webhook endpoint responses

5. **Determine Root Cause** (2 min)
   Choose path based on findings:
   
   **If all endpoints erroring:**
   - Something in common request path broken
   - Check recent deployment: `git log --oneline -5`
   - Rollback if deployed in last 5 minutes
   
   **If extract service only:**
   - Check Anthropic API status
   - Verify extraction model is loaded
   - Check for resource exhaustion
   
   **If fraud service only:**
   - Check fraud model deployment
   - Verify database queries
   - Check external dependencies

6. **Execute Fix** (5 min based on root cause)
   
   *Option A: Rollback recent deployment*
   ```bash
   # Get previous deployment
   git log --oneline -1
   # Verify it's safe to rollback
   # Execute rollback on Railway.app
   # Verify in dashboard (error rate drops)
   ```
   
   *Option B: Restart service*
   ```bash
   # For Railway.app
   # Use dashboard to redeploy current version
   # Triggers fresh container start
   # Monitor metrics during restart
   ```
   
   *Option C: Temporary configuration*
   ```bash
   # Reduce inference batch size (faster responses)
   # Increase timeout thresholds (fewer errors)
   # Disable problematic feature flag
   # (Changes applied via environment variables)
   ```

7. **Verify Resolution** (2 min)
   - Watch error rate drop in Prometheus
   - Should drop within 30-60 seconds
   - Confirm no cascading errors
   - Run health check: `curl https://api.88i.sinistro.app/health`
   - Check response is `{"status": "ok"}`

8. **Post-Incident**
   - Document which fix worked
   - Note timeline (detect to resolve)
   - Create action item to prevent recurrence
   - Schedule post-mortem if > 5 minute impact

**Decision Tree:**
```
Error Rate High?
├─ All endpoints? → Check deployment → Rollback?
├─ Extract only? → Check Anthropic → Restart service?
├─ Fraud only? → Check model → Restart service?
└─ Intermittent? → Check resource contention → Scale up?
```

**Key Metrics to Monitor:**
- `rate(errors_total[1m])` - Should drop to <1%
- `rate(requests_total[1m])` - Should maintain normal rate
- `histogram_quantile(0.95, request_duration)` - Should remain normal

**Common Pitfalls:**
- ❌ Panicking and restarting everything
- ❌ Not checking dependencies first
- ✅ Checking one thing at a time
- ✅ Having rollback plan ready

---

**Runbook 2: High Latency Incident (10 minutes)**

**Trigger:** P95 latency > 200ms for 10 minutes

**Expected Duration:** 10-30 minutes to investigate and fix

**Step-by-Step:**

1. **Verify Alert** (1 min)
   - Check latency histogram from dashboard
   - Look at P50, P95, P99 percentiles
   - Is it all endpoints or specific ones?
   - Compare to baseline (should be P95 <100ms for Extract, <150ms for Fraud)

2. **Identify Bottleneck** (3 min)
   - Run latency breakdown query:
     ```
     histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))
     by (service)
     ```
   - Which service is slow? (Extract, Fraud, or both)
   - Check request queue depth: `queue_depth{service="..."}`
   - Check CPU and memory usage

3. **Database Performance Check** (2 min)
   - Query database metrics:
     ```
     rate(db_query_duration_seconds_bucket[5m]) > 0.1
     ```
   - Any slow queries? (>100ms)
   - Check connection pool: `db_connections_total` vs `db_connections_max`
   - Verify database is responding

4. **External Service Latency** (2 min)
   - Check Anthropic API response time
   - Use Langfuse dashboard to see inference latency
   - Check if rate limiting triggered
   - Verify network conditions

5. **Resource Utilization** (2 min)
   - CPU usage: Should be <60% normally
   - Memory: Should be <500MB normally
   - Check if approaching limits
   - Look at garbage collection (GC) pauses

6. **Root Cause Analysis** (2 min)
   
   **If database slow:**
   - Run slow query log: `SELECT * FROM pg_stat_statements WHERE mean_time > 100`
   - Look for queries accessing wrong indexes
   - Check for table locks
   - **Fix:** Add index, update query, or scale database
   
   **If external API slow:**
   - Check Anthropic status page
   - May need to retry with backoff
   - Possibly reduce batch size
   - **Fix:** Implement caching, reduce payload size
   
   **If CPU high:**
   - Look for CPU-bound operations
   - Check inference batch size
   - **Fix:** Reduce batch size, scale up instances
   
   **If memory high:**
   - Check for memory leak
   - Look at cache size
   - **Fix:** Restart service, adjust cache size

7. **Execute Fix** (10 min)
   
   *Database optimization:*
   ```sql
   -- Add missing index
   CREATE INDEX idx_claims_status_date 
   ON claims(status, created_date);
   
   -- Verify improvement
   EXPLAIN ANALYZE [slow query];
   ```
   
   *Reduce inference batch size:*
   ```bash
   export INFERENCE_BATCH_SIZE=1  # Reduce from 5
   export INFERENCE_TIMEOUT=5000   # Increase timeout
   # Redeploy on Railway.app
   ```
   
   *Scale up:*
   ```bash
   # Increase Railway.app CPU and memory
   # Monitor latency improvement
   # Should see improvement within 1-2 minutes
   ```

8. **Verify Resolution** (3 min)
   - Watch P95 latency drop in Prometheus
   - Run synthetic requests and measure
   - Confirm no error rate spike
   - Health check: `curl https://api.88i.sinistro.app/health`

**Key Metrics:**
- `histogram_quantile(0.95, request_duration_seconds)` - Should return to <150ms
- `rate(requests_total[1m])` - Throughput should be stable
- `process_resident_memory_bytes` - Memory should be stable
- `system_cpu_usage` - CPU should drop

---

**Runbook 3: Database Issues (10 minutes)**

**Trigger:** Database connection failures, query timeouts, or high connection count

**Expected Duration:** 15-45 minutes (may require DBA or database scaling)

**Step-by-Step:**

1. **Verify Database Connectivity** (1 min)
   ```bash
   # Check if database is reachable
   psql -h [DB_HOST] -U [DB_USER] -d [DB_NAME] -c "SELECT 1;"
   
   # Expected: Should return "1" within 1 second
   ```

2. **Check Connection Pool Status** (2 min)
   - Query application metrics:
     ```
     db_connections_open
     db_connections_max
     db_connections_waiting
     ```
   - If `db_connections_open` near `db_connections_max`:
     - Connection pool exhausted
     - Clients waiting for connection
     - New requests queued

3. **Identify Problem Type** (2 min)
   
   **Scenario A: Connection Pool Exhausted**
   - Symptoms: `db_connections_open >= db_connections_max`
   - Check: `SELECT count(*) FROM pg_stat_activity;` on database
   - May see hanging connections
   
   **Scenario B: Slow Queries**
   - Symptoms: Connections held for long time
   - Check: `SELECT pid, query, query_start FROM pg_stat_activity WHERE state != 'idle';`
   - Long-running queries blocking others
   
   **Scenario C: Database Overload**
   - Symptoms: High CPU and memory on database
   - Check: Database monitoring tools (Supabase dashboard)
   - May need to optimize indexes or queries

4. **Investigate Active Queries** (2 min)
   ```sql
   -- Check for long-running queries
   SELECT pid, usename, query, query_start, 
          now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY query_start;
   
   -- Check for locks
   SELECT * FROM pg_locks 
   JOIN pg_stat_activity ON pg_locks.pid = pg_stat_activity.pid;
   ```

5. **Execute Fix** (Varies)
   
   *Kill long-running query:*
   ```sql
   -- WARNING: Use only if query is stuck/runaway
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE query LIKE '%specific query%'
   AND pid != pg_backend_pid();
   ```
   
   *Increase connection pool:*
   ```bash
   export DATABASE_POOL_SIZE=20  # Increase from 10
   # Redeploy application
   # Monitor connection usage
   ```
   
   *Scale database:*
   ```bash
   # In Supabase dashboard:
   # 1. Click database
   # 2. Settings → Instance size
   # 3. Scale up if needed
   # Takes 5-10 minutes to apply
   ```
   
   *Restart database:*
   ```bash
   # Last resort if database unresponsive
   # In Supabase dashboard:
   # 1. Click database
   # 2. Settings → Restart database
   # WARNING: Brief downtime (1-2 min)
   ```

6. **Verify Recovery** (5 min)
   - Check connection count: `db_connections_open` should drop
   - Run test query: Should complete < 100ms
   - Monitor error rate: Should drop to normal
   - Check application logs: Should show recovery

**Key Metrics:**
- `db_connections_open` - Should be <20 normally
- `db_query_duration_seconds` - Queries should complete quickly
- `db_connection_errors_total` - Should be 0 or very low

---

**Runbook 4: Memory Leak / High Memory Usage (10 minutes)**

**Trigger:** Memory usage > 80% of limit, or consistently growing

**Expected Duration:** 15-30 minutes (may require restart)

**Step-by-Step:**

1. **Verify Memory Leak vs. Normal Growth** (2 min)
   - Check memory trend over time
     ```
     process_resident_memory_bytes (gauge - only current value)
     ```
   - Look at memory growth rate
   - Is it stabilizing or continuously increasing?
   - Compare to baseline (should be ~300MB normally)

2. **Identify Memory Consumer** (3 min)
   - Check application profiling metrics (if available)
   - Look for cache size: `cache_entries_total`
   - Check model size in memory
   - Look for unbounded data structures

3. **Assess Severity** (1 min)
   - If < 80%: Monitor for now, plan investigation
   - If 80-90%: Start investigation, prepare for restart
   - If > 90%: Consider immediate restart, alert on-call

4. **Collect Debug Information** (3 min)
   ```bash
   # Take heap dump (if running JVM)
   jmap -heap [PID]
   
   # Or for Python/Go:
   # Check resident memory vs cache size
   # Look for unbounded queues
   
   # Check logs for clues
   grep -i "cache\|queue\|buffer" /var/log/88i-sinistro/app.log | tail -20
   ```

5. **Determine Root Cause** (2 min)
   
   **If cache growing:**
   - Check cache size configuration
   - May need to reduce cache TTL
   - Or implement cache eviction policy
   
   **If model staying large:**
   - Normal (ML models are memory-intensive)
   - Only alert if exceeding expected size
   
   **If queue growing:**
   - Messages not being processed
   - Check Inngest queue status
   - May need to process backlog
   
   **If unbounded growth:**
   - Likely a memory leak
   - Needs code investigation and restart

6. **Execute Immediate Fix** (5-10 min)
   
   *Reduce cache size:*
   ```bash
   export CACHE_MAX_SIZE=1000  # Reduce from 10000
   # Redeploy
   # Monitor memory
   ```
   
   *Restart service (if suspected leak):*
   ```bash
   # On Railway.app dashboard
   # Click "Redeploy" button
   # Service restarts with fresh memory
   # Memory should drop to ~300MB
   # Takes 2-3 minutes
   ```
   
   *Scale up memory (temporary):*
   ```bash
   # In Railway.app settings
   # Increase RAM allocation from 512MB to 1GB
   # Buys time for root cause investigation
   # Should be treated as temporary fix
   ```

7. **Verify Fix** (2 min)
   - Check memory usage drops
   - Confirm error rate normal
   - Monitor growth rate (should be flat)

**Key Metrics:**
- `process_resident_memory_bytes` - Should be <500MB normally
- `cache_size_bytes` - Should be <100MB
- Memory growth trend - Should be flat, not climbing

---

#### Topic 3: Common Issues & Solutions (20 minutes)

**Content:**

**Common Issue 1: "High Error Rate" - What to Do**

| Symptom | Likely Cause | Investigation | Fix | Escalate? |
|---------|------------|----------------|-----|-----------|
| All endpoints returning 500 | Recent deployment | Check git log | Rollback | If > 5 min |
| Extract only failing | Anthropic API issue | Check external status | Wait/retry | If > 15 min |
| Fraud only failing | Model not loaded | Check logs | Redeploy | If > 10 min |
| 4xx errors (400, 403, etc) | Client sending bad requests | Check request logs | Contact client | No |
| Intermittent failures | Resource contention | Check CPU/memory | Scale up | If recurring |

**Common Issue 2: "Slow Requests" - What to Do**

| Symptom | Likely Cause | Check | Fix | Time |
|---------|------------|-------|-----|------|
| All requests slow | Database slow | Query performance | Add index | 10 min |
| Extract slow, Fraud OK | Anthropic rate limit | API status page | Reduce batch size | 5 min |
| Intermittently slow | GC pauses | Memory usage graph | Increase heap | 5 min |
| One user slow | Their network | Traceroute test | Not our problem | 0 min |
| Consistent P99 slow | Normal tail behavior | Percentile graphs | Acceptable | 0 min |

**Common Issue 3: "Alert Every 5 Minutes" - What to Do**

This is called "alert fatigue" and is dangerous because people ignore alerts.

| Problem | Cause | Solution |
|---------|-------|----------|
| Alert fires, resolves, fires again | Root cause not fixed | Fix underlying issue, not symptom |
| Alert threshold too aggressive | Threshold set too low | Increase threshold by 20% |
| Alert fires on boot | Service startup causes spike | Exclude first 5 min after deploy |
| Legitimate spike expected | Expected traffic pattern | Create suppression window or scheduled maintenance |

**Troubleshooting Checklist:**

When an incident is reported:

1. [ ] Check if this is a real incident (not false alarm)
   - Are errors actually happening now?
   - Or is this old error log?
   - Rule out cached data

2. [ ] Determine scope of impact
   - [ ] All users or subset?
   - [ ] All features or specific feature?
   - [ ] How many requests affected?

3. [ ] Check if issue is in our system
   - [ ] Check external dependencies first
   - [ ] Check application logs
   - [ ] Check database connectivity
   - [ ] Rule out edge cases / specific data

4. [ ] Identify root cause
   - [ ] Recent deployment? Check git log
   - [ ] Resource exhaustion? Check CPU/memory
   - [ ] Database issue? Check connection pool
   - [ ] External service down? Check status pages

5. [ ] Execute fix carefully
   - [ ] Document what you're about to do
   - [ ] Have rollback plan ready
   - [ ] Start from safest fix first (waiting, config change)
   - [ ] Only restart as last resort

6. [ ] Verify fix works
   - [ ] Watch metrics for 2 minutes
   - [ ] Confirm no error spike
   - [ ] Test functionality

7. [ ] Document the incident
   - [ ] What was wrong
   - [ ] What you did
   - [ ] How long it took
   - [ ] What to prevent it next time

**When to Escalate:**

- P1 issues: Escalate immediately (you shouldn't handle alone)
- P2 issues: Escalate if > 15 minutes with no progress
- P3 issues: Handle independently, escalate if stuck

**Red Flags - Escalate Immediately:**

- [ ] Multiple services failing
- [ ] Database appears down
- [ ] Can't connect to production environment
- [ ] Considering major rollback
- [ ] Uncertain about safe fix
- [ ] Issue > 5 minutes with increasing impact

**Handout Materials:**
- Troubleshooting decision tree (flowchart)
- Common issues quick reference (card)
- Escalation decision guide
- Red flag list (printed)

#### Topic 4: Practice Incident Simulation (20 minutes)

**Content:**

This hands-on exercise allows participants to practice incident response in a safe environment before handling real production incidents.

**Scenario:** Extract service is showing high error rate (8%) after a recent deployment.

**Timeline:**
- T+0 (min 0): Alert fires → Participant receives PagerDuty page
- T+5 (min 5): Participant must ack alert and post initial response
- T+10 (min 10): Trainer injects secondary clue (logs show Anthropic timeout)
- T+15 (min 15): Trainer asks what participant would do
- T+20 (min 20): Participant executes chosen action (rollback or config fix)
- T+25 (min 25): Trainer confirms fix resolved issue
- T+30 (min 30): Debrief and discussion

**Setup (Trainer):**

Before exercise:
1. Show participant Grafana dashboard with high error rate
2. Provide access to Slack, logs, Prometheus
3. Explain: "You just received a PagerDuty page. The Extract service has high errors."
4. Set a timer for 30 minutes

**Participant Tasks:**

1. **Acknowledge Alert** (min 1)
   - Find PagerDuty alert
   - Ack it in PagerDuty
   - Post in Slack: "I'm on it, investigating"

2. **Investigate** (min 2-5)
   - Check Grafana dashboard
   - Look at error rate graph
   - Which service? (Extract)
   - Check error types in Prometheus
   - Look at application logs
   - Identify: "Anthropic API timeouts"

3. **Form Hypothesis** (min 6)
   - Suggest what might be wrong
   - Example: "Looks like Anthropic is timing out, started after recent deploy"

4. **Communicate Status** (min 7)
   - Post in Slack:
     ```
     Status: INVESTIGATING
     Symptom: Extract service returning errors
     Finding: Anthropic API timeouts in logs
     Next: Checking if recent deployment caused issue
     ```

5. **Determine Fix** (min 8-10)
   - Ask: "Should I rollback or change config?"
   - Discuss two options:
     - Option A: Rollback to previous deployment (safest)
     - Option B: Reduce batch size and retry (faster)
   - Participant chooses based on risk tolerance

6. **Execute Fix** (min 11-15)
   - If rollback: "I'm rolling back to deployment #4"
   - If config change: "I'm setting BATCH_SIZE=1 and redeploying"
   - Post command in Slack
   - Wait for change to take effect

7. **Verify Resolution** (min 16-20)
   - Watch error rate drop in Grafana
   - Confirm P95 latency normal
   - Run test: `curl https://api.88i.sinistro.app/extract` with test data
   - Confirm no new errors

8. **Post-Incident** (min 21-30)
   - Post in Slack:
     ```
     RESOLVED in 12 minutes
     Root Cause: Anthropic API timeouts after deployment
     Fix: Rollback to previous version
     Action Items:
     - Investigate root cause of timeouts in new code
     - Add timeout handling
     - Schedule post-mortem
     ```
   - Discuss with trainer what went well and what could improve

**Grading Rubric:**

| Criterion | Excellent | Good | Needs Work |
|-----------|-----------|------|-----------|
| **Time to Ack** | <1 min | 1-3 min | >3 min |
| **Investigation thoroughness** | Checked logs, metrics, dependencies | Checked 2 of 3 | Checked only 1 |
| **Root cause identification** | Correctly identified cause | Partially correct | Wrong cause |
| **Fix choice** | Safe, appropriate choice | Adequate choice | Poor/risky choice |
| **Communication** | Clear, frequent updates | Updates provided | Minimal communication |
| **Time to resolution** | <15 min | 15-25 min | >25 min |
| **Post-incident documentation** | Complete with action items | Summary provided | No documentation |

**Post-Exercise Debrief:**

Ask participant:
1. What was most challenging?
2. What tools were most helpful?
3. Would you handle this differently next time?
4. Any questions about process?
5. Confidence level (1-10) for real incident?

**Trainer Notes:**

- This is a learning exercise, not a test
- Encourage questions and discussion
- If participant gets stuck, provide hints
- Focus on process, not speed (though speed improves over time)
- Celebrate good decisions and learning from mistakes

### Materials Provided

- [ ] 6-Phase framework flowchart (printed)
- [ ] 4 Runbooks (printed, collated)
- [ ] Common issues quick reference card
- [ ] Troubleshooting decision tree
- [ ] Escalation decision guide
- [ ] Incident response templates (digital)
- [ ] Prometheus query cheat sheet
- [ ] Dashboard access credentials

### Assessment (Session 2)

**Knowledge Questions:**
1. What are the 6 phases of incident response?
2. When should you escalate a P2 incident?
3. How do you determine if the issue is in the app vs. database?
4. What is the first thing you should do when you get a P1 page?
5. Name two tools you use to investigate errors.

**Practical Simulation:**
- Participate in simulated incident scenario
- Be judged on time, process, and decision-making
- Must show understanding of runbooks
- Should ask for help when uncertain (good!)

---

## Session 3: Operational Procedures (1 hour)

### Objectives
By the end of this session, participants will be able to:
- Execute on-call handoff procedures correctly
- Perform backup verification and recovery procedures
- Execute deployment and rollback procedures
- Participate in post-incident activities
- Maintain operational documentation

### Topics

#### Topic 1: On-Call Rotation Management (15 minutes)

**Content:**

**Weekly Rotation Structure:**

The on-call rotation runs on a weekly schedule with a weekly handoff every Monday at 9 AM UTC.

```
Monday 9 AM UTC: Rotation changes
├─ Outgoing on-call: Hands off to incoming
├─ Handoff meeting: 30 minutes
├─ Verify access and tools
└─ Incoming on-call starts monitoring

Incoming on-call: Owns alerts for full week
├─ 24/7 availability during week
├─ Responds to all PagerDuty pages
├─ Documents incidents
├─ Hands off Friday evening / Saturday morning

Tuesday-Sunday: Monitoring & incident response
├─ Watch Grafana dashboard
├─ Respond to alerts within 5 minutes
├─ Update incident status
├─ Escalate if needed

Friday/Saturday evening: Handoff prep
├─ Compile incident summary
├─ Document any outstanding issues
├─ Prepare handoff notes
└─ Ensure incoming on-call has access
```

**On-Call Rotation Roles:**

1. **Primary On-Call Engineer**
   - Responsible for all alerts 24/7
   - Must respond within 5 minutes of page
   - Can escalate to secondary for complex issues
   - Own the week (can't just ignore alert)
   - Compensation: Tier 3 hourly rate + hazard pay

2. **Secondary On-Call Engineer**
   - Backup for primary
   - Engaged if primary doesn't ack within 5 minutes
   - Assists with complex issues
   - Available during business hours minimum
   - Reviews incidents for learning

3. **Escalation Manager**
   - Escalation point for P1 incidents
   - Senior engineer or manager
   - Available for critical decisions
   - Handles customer communication for P1
   - Not part of weekly rotation

4. **On-Call Coordinator (Async)**
   - Tracks on-call schedule
   - Verifies access permissions
   - Manages escalation contacts
   - One person, rotates monthly

**Escalation Paths:**

```
Alert triggers
    ↓
Primary On-Call (5 min response time)
    ↓ [if primary not responding after 5 min]
Secondary On-Call (notified by PagerDuty)
    ↓ [if issue > 15 min or critical decision needed]
Escalation Manager (paged)
    ↓ [if P1 and affecting customers]
Director / Customer Success (executive escalation)
```

**Communication Channels:**

- **Primary:** Slack #operations-incidents
  - All incident updates posted here
  - Visible to entire team
  - Creates incident thread with all context

- **Secondary:** PagerDuty
  - Automatic pages sent to on-call
  - Acknowledgment and escalation tracked
  - Mobile app for alerts even if away from desk

- **Tertiary:** Phone/SMS
  - Only for P1 escalation
  - Out-of-office backup contact
  - Rarely used

**Maintenance Windows & Break Glass:**

- **Planned Maintenance:** Schedule in advance with notice
  - Example: Database migration on Saturday 2-3 AM
  - Notify team in advance
  - On-call not expected to respond to deployment alerts
  - Escalation manager on standby

- **Break Glass Procedure** (Emergency Access):
  - If on-call unavailable in real emergency
  - Any engineer can declare "break glass"
  - All engineers paged immediately
  - Senior engineer takes command
  - Used for: Natural disaster, on-call incapacitated, etc.

**Handoff Procedure (Every Monday 9 AM UTC):**

Time: 30 minutes
Attendees: Outgoing on-call + incoming on-call + team lead

**Steps:**

1. **Review Last Week** (5 min)
   - Incidents summary: Count, severity, MTTR
   - Major incidents: Root cause, resolution
   - Preventive actions taken

2. **Outstanding Issues** (5 min)
   - Any ongoing problems?
   - Any known flaky components?
   - Any escalating trends?

3. **Verify Access & Tools** (5 min)
   - Incoming on-call can access:
     - [ ] Grafana (test: load dashboard)
     - [ ] Prometheus (test: run query)
     - [ ] PagerDuty (test: view schedule)
     - [ ] Slack channels
     - [ ] SSH to production (if applicable)
     - [ ] Railway.app dashboard
     - [ ] Supabase dashboard
   - If any access missing: Request/grant immediately

4. **Recent Changes** (5 min)
   - Recent deployments?
   - Database migrations?
   - Configuration changes?
   - New alerts added?
   - Expected load spikes?

5. **Contact Information** (3 min)
   - Escalation contacts (phone numbers)
   - Database team contact
   - External service support contacts
   - Customer support phone number
   - Verify all contacts are current

6. **Handoff Notes** (2 min)
   - Review Slack #on-call-handoff channel
   - Outgoing on-call posts summary
   - Incoming on-call acknowledges

**Handoff Checklist:**

- [ ] Last week's incident summary reviewed
- [ ] Outstanding issues discussed
- [ ] All tool access verified and working
- [ ] Recent deployments and changes reviewed
- [ ] Contact list current and shared
- [ ] Known flaky areas identified
- [ ] Escalation paths confirmed
- [ ] Monitoring status verified
- [ ] PagerDuty confirmed receiving alerts
- [ ] Slack notifications enabled

**What to Avoid:**

- ❌ Starting on-call without handoff meeting
- ❌ Not testing tool access before taking rotation
- ❌ Assuming you know what happened last week
- ❌ Skipping the contact list review
- ❌ Not posting handoff summary

**Best Practices:**

- ✅ Arrive 10 minutes early for handoff
- ✅ Ask questions about anything unclear
- ✅ Document any new learnings
- ✅ Set up desktop notifications for Slack
- ✅ Keep phone accessible during on-call
- ✅ Test all tools on day 1 of rotation

#### Topic 2: Backup & Recovery Procedures (20 minutes)

**Content:**

**Backup Strategy Overview:**

The 88i Sinistro system uses Supabase PostgreSQL which includes automated backups.

```
Database Backups:
├─ Automated daily: Every day at 2 AM UTC
├─ Point-in-time restore (PITR): Up to 7 days
├─ Manual backup: Can trigger anytime
└─ Backup location: Supabase (geographic redundancy)

Application Code:
├─ Source: GitHub repository
├─ Deployments: Railway.app (auto-builds from main)
└─ Rollback: Previous Docker image always available

Application Data:
├─ Primary: PostgreSQL database (Supabase)
├─ Cache: Redis (if used) - can be recreated
└─ Logs: Cloudflare / Railway (retention: 7 days)
```

**Backup Verification (Weekly Task):**

Every Monday at 10 AM (after handoff), verify backup health:

```bash
# Step 1: Check Supabase backup status
# 1. Go to Supabase dashboard
# 2. Click "Database" tab
# 3. Look for "Backup" section
# 4. Verify:
#    - Last backup: Should be < 24 hours old
#    - Backup size: Should be ~50MB (varies)
#    - Status: "Healthy" or "Available"

# Expected screenshot: Green checkmark next to "Last backup: [today]"
# If red or error: Escalate immediately

# Step 2: Check backup recovery capability
# (This is done monthly by on-call manager, not weekly)
```

**Recovery Procedure (In Case of Data Loss):**

**Scenario:** Database corruption detected, need to restore from backup

**Recovery Steps:**

1. **Assess Situation** (5 min)
   - How much data lost? (specific tables or entire DB)
   - How far back must we restore? (last 1 hour, 1 day, etc.)
   - How much downtime is acceptable?
   - Do we have point-in-time restore (PITR) available?

2. **Notify Stakeholders** (2 min)
   ```
   Message in #operations-incidents:
   🚨 DATABASE INCIDENT: Data corruption detected
   
   Status: INVESTIGATING RECOVERY
   Impact: [Which tables/features affected]
   Recovery Goal: Restore to [TIME] - data loss: [amount]
   ETA: [estimate]
   
   @manager notification (out of channel)
   ```

3. **Prepare for Recovery** (5 min)
   - Stop application traffic (to prevent further writes)
     ```bash
     # Deploy "maintenance mode" version
     export MAINTENANCE_MODE=true
     # Redeploy on Railway.app
     # This returns 503 to all requests
     ```
   - Notify that system is down
   - Get stakeholder approval for data loss window

4. **Execute PITR Restore** (15-30 min)
   ```
   In Supabase Dashboard:
   1. Click "Database"
   2. Click "Backups" section
   3. Choose "Point-in-Time Restore"
   4. Select recovery point:
      - Choose timestamp just before corruption
      - Example: 2026-05-27 14:30:00 UTC
   5. Click "Restore"
   6. Wait for restore to complete (usually 5-15 min)
   7. System returns to normal state at that point in time
   ```

5. **Bring Application Back Online** (2 min)
   ```bash
   # Remove maintenance mode
   export MAINTENANCE_MODE=false
   # Redeploy
   # Application comes back online
   ```

6. **Verify Data Integrity** (5 min)
   ```bash
   # Run health checks
   curl https://api.88i.sinistro.app/health
   
   # Check critical tables
   # Query: SELECT COUNT(*) FROM claims;
   # Verify count makes sense (not 0)
   
   # Check data timestamp
   # Query: SELECT MAX(created_at) FROM claims;
   # Should show timestamp of recovery point
   ```

7. **Incident Post-Mortem** (24 hours after)
   - What caused corruption? (usually: application bug, hardware failure)
   - How to prevent? (add data validation, improve monitoring)
   - Update runbooks
   - Test recovery procedure annually

**Disaster Recovery Test (Quarterly):**

Every quarter, conduct a planned DR test:

```
1. Schedule maintenance window
2. Announce to team (but not full details)
3. Create test database copy (Supabase feature)
4. Simulate incident (corrupt test DB)
5. Perform recovery procedure
6. Measure:
   - Time to restore
   - Data validation success
   - Recovery accuracy
7. Document lessons learned
8. Update recovery procedures if needed
```

**Failover Procedure (If Database Unavailable):**

If main database completely unavailable:

```
1. Check Supabase status page (is their service down?)
2. If Supabase down: All recovery must wait for their recovery
3. If our database down: Follow PITR restore above
4. Temporary: Can deploy "read-only mode" to serve cached data
5. Manual failover: Can switch to backup database (if one exists)
```

**Backup Testing Schedule:**

- **Weekly:** Verify last backup completed (Monday 10 AM)
- **Monthly:** Test restore to staging environment
- **Quarterly:** Full disaster recovery simulation
- **Annually:** Review backup strategy and RPO/RTO targets

**Key Metrics:**

- **RPO (Recovery Point Objective):** Max acceptable data loss = 24 hours
- **RTO (Recovery Time Objective):** Max acceptable downtime = 4 hours
- **Backup retention:** 7 days of PITR, 30 days of daily backups

**Common Mistakes:**

- ❌ Assuming backups are working without verification
- ❌ Not knowing how to trigger recovery
- ❌ Waiting for disaster before testing recovery
- ✅ Testing monthly in non-production environment
- ✅ Documenting recovery time during test
- ✅ Having a plan before emergency

#### Topic 3: Deployment & Rollback Procedures (15 minutes)

**Content:**

**Standard Deployment Process:**

Deployments to production use automated CI/CD on Railway.app.

```
Developer → Git Push → GitHub → Railway.app Webhook
                                  ↓
                        Build Docker Image
                                  ↓
                        Run Tests & Checks
                                  ↓
                        Push to Registry
                                  ↓
                        Deploy to Staging
                                  ↓
                        Run Smoke Tests
                                  ↓
                        Deploy to Production
                                  ↓
                        Monitor Metrics
```

**Pre-Deployment Checklist:**

Before merging code to main:

- [ ] Code reviewed by 1+ engineer
- [ ] All tests passing locally
- [ ] Staging deployment tested manually
- [ ] Breaking changes documented
- [ ] Database migrations backwards-compatible
- [ ] Configuration changes not required (or documented)
- [ ] Performance tested (no obvious slowdowns)
- [ ] Security reviewed (if touching auth/crypto)

**Deployment Health Checks:**

After deployment to production:

```
T+0 (deploy completes):
- [ ] Health check: GET /health → 200
- [ ] Error rate < 1%

T+2 minutes:
- [ ] All services responding
- [ ] Database queries working
- [ ] External integrations healthy
- [ ] No error spikes in logs

T+5 minutes:
- [ ] P95 latency normal
- [ ] Request rate normal
- [ ] Memory usage normal
- [ ] No customer complaints in support

T+15 minutes:
- [ ] All metrics look good
- [ ] Can declare deployment successful
- [ ] Log deployment in #operations
```

**Monitoring During Deployment:**

```
While deployment is in progress:
├─ Watch Grafana dashboard (auto-refresh every 30 seconds)
├─ Error rate: Should stay < 1%
├─ Latency: Should stay normal
├─ Request rate: Will drop slightly during switch-over (normal)
├─ CPU/Memory: Will briefly spike then normalize
└─ If error rate > 2%: Consider rollback
```

**Rollback Procedure:**

**When to Rollback:**

- P1 incident within 15 minutes of deployment
- Error rate > 5%
- 100% of requests failing
- Any critical system failure
- NOT for: Single failed endpoint, non-critical feature issue

**Rollback Steps (5 minutes):**

```bash
# Step 1: Declare rollback (2 min)
# Post in Slack #operations-incidents:
# 🚨 ROLLBACK: Reverting to previous version
# Reason: High error rate after deployment
# Owner: [Your name]

# Step 2: Trigger rollback on Railway.app (1 min)
# 1. Go to Railway.app dashboard
# 2. Click "Deployments" tab
# 3. Find previous successful deployment (green checkmark)
# 4. Click "Revert"
# 5. Confirm "Yes, rollback"
# System begins deploying previous version

# Step 3: Monitor recovery (2 min)
# Watch error rate drop in Grafana
# Should drop within 1-2 minutes
# Confirm metrics return to normal

# Step 4: Post-rollback actions (5 min - do after stability)
# - Notify stakeholders: "Issue identified, rolled back successfully"
# - Create incident ticket
# - Schedule investigation meeting
# - Prevent same code from being deployed again
```

**Post-Rollback Investigation:**

After rollback and things are stable:

1. Compare deployments
   ```bash
   git log --oneline -2  # See current vs. previous
   git diff [commit1] [commit2]  # See what changed
   ```

2. Review the problematic code
   - What feature was added?
   - What changed in behavior?
   - Were there database migrations?
   - Were there configuration changes?

3. Identify root cause
   - Bug in new code?
   - Incompatible with current database?
   - Performance regression?
   - Missing error handling?

4. Create fix
   - Fix the bug
   - Add test to catch this in future
   - Add monitoring for this scenario

5. Re-deploy
   - Use same deployment process
   - Extra careful review
   - Extra monitoring time (30 min instead of 15 min)

6. Document
   - Create post-mortem or incident note
   - Link to code review
   - Add to "lessons learned" wiki

**Zero-Downtime Deployment Strategy:**

```
Two-version model (rolling deployment):

Before:  Version A (100% of traffic)
          ↓
Step 1:  Spin up Version B (new code)
         (Kuberenetes/Container orchestration would do this)
         Version A: 100%
         Version B: 0%
          ↓
Step 2:  Shift traffic gradually
         Version A: 95%
         Version B: 5%
         (If errors increase, stop and rollback)
          ↓
Step 3:  Continue shifting
         Version A: 50%
         Version B: 50%
         (Monitor health at each step)
          ↓
Step 4:  Switch fully
         Version A: 0%
         Version B: 100%
         (Old version can be kept for instant rollback)
          ↓
After:   Version B only (can remove Version A safely)

This approach ensures:
- No downtime
- Quick rollback if needed
- Gradual traffic shift
- Full monitoring throughout
```

**Deployment Frequency:**

- **Typical:** 3-5 deployments per day (normal)
- **During crisis:** Can do emergency deployments (rare)
- **Maintenance windows:** Deployments outside business hours

**Common Rollback Mistakes:**

- ❌ Clicking "Redeploy" (redeploys same broken version)
- ❌ Forgetting to post in Slack (team doesn't know)
- ❌ Waiting too long (error rate becomes unacceptable)
- ❌ Manually reverting code (should use Railway.app rollback)
- ✅ Checking what changed before investigating
- ✅ Reverting to stable version
- ✅ Notifying team immediately

#### Topic 4: Post-Incident Activities (10 minutes)

**Content:**

**Post-Incident Checklist:**

After any incident (even small ones), complete these steps:

- [ ] **Within 1 hour:** Post incident summary in Slack
  ```
  📋 INCIDENT SUMMARY
  Duration: [X minutes]
  Severity: P1/P2/P3
  Root Cause: [Brief description]
  Impact: [Users/features affected]
  Resolution: [What we did]
  ```

- [ ] **Within 24 hours:** Schedule post-mortem meeting
  - Include: on-call engineer, team lead, product owner, any relevant specialists
  - Duration: 30-60 minutes
  - Goal: Understand, learn, prevent recurrence

- [ ] **Within 48 hours:** Complete post-mortem document
  - Timeline of incident
  - Root cause analysis
  - Why we didn't catch this
  - Action items to prevent

- [ ] **Within 1 week:** Complete action items
  - Add monitoring alert
  - Update runbooks
  - Fix underlying code
  - Add tests

**Post-Mortem Template:**

```markdown
# Incident Post-Mortem

**Incident:** [Title]
**Date:** [Date]
**Duration:** [X minutes]
**Severity:** P1/P2/P3

## Timeline

| Time | Event |
|------|-------|
| 14:32 UTC | Error rate alert triggered (> 5%) |
| 14:33 UTC | On-call engineer paged and acknowledged |
| 14:38 UTC | Identified as Anthropic API timeout |
| 14:42 UTC | Decided to reduce batch size |
| 14:45 UTC | Deployed fix |
| 14:47 UTC | Error rate returned to normal |
| 14:50 UTC | Monitoring confirmed stable |
| **Total Duration** | **18 minutes** |

## Root Cause

The deployment at 14:30 increased batch size from 3 to 5 for better throughput. However, this caused average request size to exceed Anthropic API timeout threshold (10 seconds). The API started timing out, which our application didn't retry properly, resulting in errors.

## Why It Wasn't Caught

1. Load testing was done with small batch sizes (default 3)
2. No synthetic test for Anthropic timeout scenario
3. Default timeout not appropriate for larger batches
4. No pre-deployment load test before rolling out

## Resolution

Quick fix: Reduced batch size back to 3. Error rate immediately returned to normal.

Better fix: Add timeout handling, make batch size configurable, add load test for batch size changes.

## Action Items

- [ ] Code: Add retry logic for Anthropic timeouts (Engineer A, 2 days)
- [ ] Testing: Add load test for batch size > 3 (Engineer B, 2 days)
- [ ] Monitoring: Add alert for Anthropic timeout rate (On-call, 1 hour)
- [ ] Runbook: Add "Anthropic timeouts" scenario (Engineer A, 1 day)
- [ ] Review: Re-examine all batch size settings (Team lead, 1 day)

## Lessons Learned

1. Always test with production-like batch sizes
2. External API timeouts are failure mode to test
3. Batch size changes need extra review
4. Could have been caught with pre-deployment load test

## Attendees

- On-call engineer (incident responder)
- Engineering team lead
- Feature owner
- Senior engineer (reviewer)

**Meeting Date:** 2026-05-28, 10 AM UTC
**Duration:** 45 minutes
```

**Knowledge Base Updates:**

After incident, update documentation:

1. **Update Runbooks:**
   - Add new scenario if not covered
   - Add this incident to examples
   - Add prevention step to related runbook

2. **Update Architecture Docs:**
   - Document limitation discovered (e.g., "Anthropic has 10s timeout")
   - Add to known issues list
   - Link to related incidents

3. **Update Operations Wiki:**
   - Add this incident to "incident history"
   - Add to "lessons learned" page
   - Update best practices if relevant

4. **Update Monitoring:**
   - Add new alert if missing
   - Add new dashboard panel if helpful
   - Document metric thresholds

**Preventing Recurrence:**

Common prevention strategies:

| Problem | Prevention | Time to Implement |
|---------|-----------|-------------------|
| Code bug | Add test, code review, QA | 2-4 hours |
| Missing monitoring | Add alert, add dashboard panel | 30 min |
| Design flaw | Refactor, test alternative approach | 2-5 days |
| Operational procedure issue | Document, training, checklist | 1-2 hours |
| Insufficient resources | Capacity planning, scaling | 2-7 days |

**Blameless Post-Mortem Culture:**

Important: Post-mortems are NOT about finding blame.

- ✅ Focus on: Systems, processes, tools, documentation
- ✅ Ask: "How could the system have prevented this?"
- ✅ Celebrate: "This revealed an important gap we can fix!"
- ❌ Don't: Blame individual engineers
- ❌ Don't: Punish mistakes
- ❌ Don't: Use post-mortem for performance reviews

The goal is to make the system more resilient, not to assign blame.

### Materials Provided

- [ ] On-call rotation schedule (posted in Slack)
- [ ] Handoff checklist (printed, laminated)
- [ ] Backup & recovery guide (PDF)
- [ ] Deployment checklist (printed)
- [ ] Rollback decision guide
- [ ] Post-mortem template (digital + printed)
- [ ] Knowledge base update guide
- [ ] Contact list (printed, sealed for security)

### Assessment (Session 3)

**Knowledge Questions:**
1. What day and time is the on-call handoff?
2. How do you trigger a rollback on Railway.app?
3. When should you escalate to the escalation manager?
4. What is the first thing to do in a post-mortem?
5. How often should backup recovery be tested?

**Practical Tasks:**
1. Demonstrate on-call handoff checklist
2. Practice with rollback scenario
3. Draft a post-mortem outline
4. Verify backup status in Supabase dashboard

---

## Competency Checklist: Operations Readiness

**By the end of training, participants should be able to do the following 10 items without assistance:**

### Tier 1: Foundation (Required for all)

1. **[ ] Interpret Grafana dashboards and identify anomalies**
   - Can look at dashboard and identify when something is wrong
   - Understands what each metric means
   - Can compare current vs. historical baseline
   - *Validation:* Show dashboard, ask "what's wrong here?"

2. **[ ] Understand and execute the 6-phase incident response framework**
   - Can explain all 6 phases in order
   - Knows what happens in each phase
   - Can execute from detection through post-mortem
   - *Validation:* Walk through framework without notes

3. **[ ] Execute all 4 runbook scenarios without assistance**
   - High error rate runbook
   - High latency runbook
   - Database issues runbook
   - Memory leak runbook
   - *Validation:* Run simulated incident successfully

4. **[ ] Perform basic troubleshooting using logs and metrics**
   - Can locate and read application logs
   - Can write Prometheus queries
   - Can correlate multiple data sources
   - Can identify root cause patterns
   - *Validation:* Given an incident scenario, diagnose it correctly

5. **[ ] Know when to escalate vs. resolve independently**
   - Understands P1/P2/P3 definitions
   - Knows escalation paths
   - Can make good judgment calls
   - Knows when to ask for help
   - *Validation:* Present 5 scenarios, ask escalation decision

### Tier 2: Operational (Required for on-call rotation)

6. **[ ] Execute rollback procedures safely and quickly**
   - Can trigger rollback without breaking system
   - Understands rollback risks and benefits
   - Can verify rollback was successful
   - Knows when rollback is appropriate
   - *Validation:* Practice rollback procedure

7. **[ ] Communicate status updates effectively to stakeholders**
   - Can draft clear incident updates
   - Knows what information stakeholders need
   - Uses appropriate language (not too technical, not too vague)
   - Updates frequently enough
   - *Validation:* Draft 3 incident status updates

8. **[ ] Participate in post-mortems effectively**
   - Can contribute to root cause analysis
   - Understands blameless approach
   - Can suggest prevention measures
   - Can commit to action items
   - *Validation:* Participate in mock post-mortem

### Tier 3: Professional (Best practices)

9. **[ ] Follow on-call procedures correctly**
   - Completes handoff checklist before taking rotation
   - Documents incidents properly
   - Follows communication procedures
   - Escalates appropriately
   - *Validation:* Complete actual handoff successfully

10. **[ ] Document issues and solutions properly for knowledge base**
    - Creates clear, searchable documentation
    - Links incidents to runbooks
    - Updates procedures based on learnings
    - Contributes to team knowledge
    - *Validation:* Draft runbook update or wiki entry

---

## Training Completion & Certification

**Prerequisites for On-Call Rotation:**

Before an engineer can join on-call rotation, they must:

1. ✅ Complete all 3 training sessions
2. ✅ Pass knowledge assessment (80% required)
3. ✅ Pass practical simulation (resolution time < 15 min)
4. ✅ Receive sign-off from trainer/manager
5. ✅ Complete first on-call rotation shadowing

**Certification Timeline:**

- Session 1: Week 1 (Monday)
- Session 2: Week 2 (Wednesday)
- Session 3: Week 3 (Friday)
- Assessment & Certification: Week 3 (Friday evening)
- Shadowing rotation: Week 4
- Independent on-call: Week 5

**Recurring Training:**

- **Annual refresher:** All on-call engineers retrain once per year
- **New procedures:** Training when major changes happen
- **New engineer onboarding:** 3-session training required

---

## Key Resources & Reference Materials

**External Documentation:**

- Prometheus Documentation: https://prometheus.io/docs/
- Grafana Dashboard Guide: https://grafana.com/docs/grafana/latest/
- Railway.app Deployment Docs: https://docs.railway.app/
- Supabase PostgreSQL Docs: https://supabase.com/docs/guides/database
- PagerDuty Integration Guide: https://support.pagerduty.com/

**Internal Documentation:**

- `docs/MONITORING_SETUP.md` - Detailed monitoring configuration
- `docs/INCIDENT_RESPONSE.md` - Extended incident response procedures
- `docs/RUNBOOKS.md` - Additional runbook scenarios
- `docs/DISASTER_RECOVERY.md` - Disaster recovery procedures
- `docs/PRODUCTION_CHECKLIST.md` - Pre-launch checklist

**Training Materials Repository:**

Location: `docs/training/` (this directory)

- `OPERATIONS_TRAINING.md` - This file
- `ON_CALL_SCHEDULE.md` - On-call rotation schedule and procedures
- `TRAINING_COMPLETION.md` - Participant records and certification

**Support Contacts:**

- Operations Manager: [Contact information]
- On-Call Lead: [Contact information]
- Infrastructure Team: [Slack channel]
- Emergency Escalation: [Phone number, for P1 only]

---

## Appendix A: Glossary of Terms

| Term | Definition |
|------|-----------|
| **Apdex Score** | Application Performance Index (0-1 scale, 1=perfect) |
| **Baseline** | Normal/expected performance level |
| **Canary Deployment** | Rolling out changes to small % of users first |
| **Cascade Failure** | One failure causes other failures (domino effect) |
| **Flapping** | Alert repeatedly turning on and off |
| **Graceful Degradation** | System reduces features but stays partially available |
| **Hot Standby** | Backup system ready to take over instantly |
| **MTTR** | Mean Time To Recovery (average incident duration) |
| **PagerDuty** | On-call management and alerting platform |
| **PITR** | Point-In-Time Restore (recovery to specific moment) |
| **RPO** | Recovery Point Objective (max acceptable data loss) |
| **RTO** | Recovery Time Objective (max acceptable downtime) |
| **SLA** | Service Level Agreement (promised uptime/performance) |
| **Synthetic Test** | Automated test simulating user behavior |

---

## Appendix B: Training Schedule Template

**Month:** June 2026

| Week | Monday | Wednesday | Friday |
|------|--------|-----------|---------|
| Week 1 | Session 1 (9-10 AM) | - | - |
| Week 2 | - | Session 2 (10 AM-11:30 AM) | - |
| Week 3 | - | - | Session 3 + Assessment (2-4 PM) |
| Week 4 | [Engineer A] Shadowing | [Engineer B] Shadowing | Debrief |

---

**Document Version:** 1.0  
**Last Updated:** May 27, 2026  
**Next Review:** August 2026  
**Maintained By:** Operations Manager
