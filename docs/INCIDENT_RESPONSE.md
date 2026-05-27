# 88i Sinistro API - Incident Response Procedures

Comprehensive incident response procedures for managing production incidents in the 88i Sinistro API.

---

## Response Team Structure

### Roles & Responsibilities

#### Incident Commander (IC)
- **Responsibility**: Overall incident management and coordination
- **Authority**: Make tactical decisions about mitigation strategies
- **Duration**: Entire incident until resolution
- **Key Tasks**:
  - Initiate incident response
  - Coordinate between technical team and communications team
  - Make go/no-go decisions for mitigations
  - Authorize escalations
  - Declare incident resolved

#### Lead Investigator / Technical Lead
- **Responsibility**: Lead technical investigation and root cause analysis
- **Duration**: From Initial Response through Investigation phases
- **Key Tasks**:
  - Execute incident runbooks
  - Analyze logs and metrics
  - Coordinate with specialists
  - Present findings to IC

#### Communications Lead
- **Responsibility**: External and internal communications
- **Duration**: Entire incident
- **Key Tasks**:
  - Update status page every 15-30 minutes
  - Send templated communications to stakeholders
  - Monitor and respond to customer inquiries
  - Prepare post-incident summary

#### Subject Matter Experts (SMEs)
- **Database SME**: Database connectivity, query performance, recovery
- **Infrastructure SME**: Kubernetes, networking, resource scaling
- **Application SME**: Code behavior, feature flags, recent deployments
- **Security SME**: Breach assessment, impact analysis, containment

### Escalation Levels

```
Individual Contributor (IC)
    ↓ (after 15-30 min without progress)
On-Call Engineer / Technical Lead
    ↓ (after 30-60 min without progress)
Engineering Manager / Team Lead
    ↓ (critical incidents or multi-team impact)
Director / VP Engineering
    ↓ (company-level impact)
Executive Leadership / PR Team
```

---

## Six-Phase Response Procedures

### Phase 1: Detection (0-5 minutes)

**Goal**: Confirm incident and establish communication channels

**Timeline**: 0-5 minutes

**Procedures**:

1. **Alert Verification**
   - Confirm alert is not a false positive
   - Check 2+ independent data sources (metrics, logs, dashboard)
   - Verify with health check endpoint: `curl http://localhost:9090/health`

2. **Incident Classification**
   - Determine severity level (P1/P2/P3/P4)
   - Identify affected systems and scope
   - Estimate impact (number of users, SLAs violated)

3. **Initiate Response**
   - Declare incident in PagerDuty/incident management system
   - Create incident Slack channel: `#incident-YYYY-MM-DD-HHmm`
   - Add IC, Lead Investigator, and Communications Lead
   - Notify on-call team via PagerDuty

4. **Initial Status Page Update**
   - Post "Investigating" status to public status page
   - Note affected service and status
   - Example: "We are investigating elevated error rates on the API"

**Decision Gate**: Proceed to Phase 2 once incident confirmed and team assembled

---

### Phase 2: Initial Response (5-15 minutes)

**Goal**: Stabilize situation and prevent further degradation

**Timeline**: 5-15 minutes from detection

**Procedures**:

1. **Immediate Mitigation Attempt** (if obvious solution exists)
   - **Recent Deployment**: Rollback immediately
     ```bash
     kubectl rollout undo deployment/sinistro-api -n production
     ```
   - **Service Down**: Restart application
     ```bash
     kubectl rollout restart deployment/sinistro-api -n production
     ```
   - **Resource Exhaustion**: Scale up
     ```bash
     kubectl scale deployment sinistro-api -n production --replicas=10
     ```

2. **Activate War Room** (for P1 incidents)
   - Start Zoom conference: https://zoom.us/j/INCIDENT_ZOOM_ID
   - Share Slack channel and incident dashboard
   - Establish communication cadence (updates every 5 minutes during active response)

3. **Collect Initial Context**
   - Capture screenshots of metrics dashboard
   - Note any recent changes (deployments, config changes, traffic patterns)
   - Check status of all dependent services
   - Document when incident started and first indicators

4. **Parallel Investigation**
   - Lead Investigator starts reviewing relevant logs
   - SMEs begin checking their domains
   - Collect resource metrics (CPU, memory, disk, network)

5. **Communications**
   - Send initial status update (template provided below)
   - Update status page every 5 minutes
   - Prepare customer communication if needed

**Decision Gate**: If immediate mitigation succeeds, move to Phase 3 (Mitigation/Resolution). Otherwise, proceed to Phase 3 (Investigation).

---

### Phase 3: Investigation (15-60+ minutes)

**Goal**: Identify root cause and determine appropriate mitigation

**Timeline**: Starts at 15 minutes, continues until root cause identified

**Procedures**:

1. **Systematic Troubleshooting** (follow appropriate runbook)
   - Execute steps from: docs/RUNBOOKS.md
   - Document each finding in incident ticket
   - Use structured investigation approach:
     - Check logs for errors
     - Review metrics (CPU, memory, disk, network)
     - Query database for performance issues
     - Review recent changes

2. **Parallel Tracks**
   - **Logs Analysis**: Search for error patterns, stack traces, anomalies
     ```bash
     kubectl logs -n production -l app=sinistro-api --since=30m | grep ERROR | tail -100
     ```
   - **Metrics Analysis**: Correlate with error rate, latency, resource usage
   - **Dependency Check**: Verify all external services are operational
   - **Code Review**: Check recent commits for suspicious changes

3. **Hypothesis Testing**
   - Form hypothesis based on evidence
   - Test hypothesis with small-scale actions
   - Gather data to confirm or refute
   - Document reasoning for post-mortem

4. **Escalate if Needed**
   - After 15-20 minutes without clear root cause: escalate to team lead
   - Bring in additional SMEs for their domains
   - Consider emergency war room if not already active

5. **Regular Status Updates**
   - Update status page every 15 minutes with progress
   - Example: "Root cause identified: High query latency on user-lookup endpoint. Analyzing solution options."

**Decision Gate**: Once root cause identified, move to Phase 4 (Mitigation). If unable to identify after 60+ minutes, escalate to engineering director.

---

### Phase 4: Mitigation (Starts when root cause identified)

**Goal**: Reduce or eliminate user impact

**Timeline**: Variable (5 minutes to several hours depending on fix)

**Procedures**:

1. **Risk Assessment**
   - Evaluate each mitigation option:
     - Quick fix (15-30 min deployment)
     - Workaround (disable feature, scale resources)
     - Temporary patch (hot fix without full testing)
     - Wait for normal fix (risky, only if impact is low)

2. **Implement Mitigation**
   - **For Code Issues**:
     ```bash
     # Option 1: Rollback
     kubectl rollout undo deployment/sinistro-api -n production
     
     # Option 2: Feature flag (disable problematic feature)
     kubectl set env deployment/sinistro-api -n production FEATURE_X_ENABLED=false
     ```
   - **For Infrastructure Issues**:
     ```bash
     # Scale up
     kubectl scale deployment sinistro-api -n production --replicas=10
     
     # Adjust resources
     kubectl set resources deployment sinistro-api -n production \
       --requests=cpu=2,memory=2Gi --limits=cpu=4,memory=4Gi
     ```
   - **For Database Issues**:
     ```bash
     # Clean up connections
     kubectl exec -it postgres-pod -n production -- \
       psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"
     
     # Add index
     kubectl exec -it postgres-pod -n production -- \
       psql -c "CREATE INDEX CONCURRENTLY idx_field ON table(field);"
     ```

3. **Validation**
   - Monitor metrics for improvement
   - Verify service health: `curl http://localhost:9090/health`
   - Check error rate, latency, and resource usage
   - Allow 5 minutes for metrics to stabilize

4. **Success Criteria**
   - Error rate returns to baseline (<1%)
   - P95 latency returns to normal (<100ms)
   - No new errors introduced
   - All health checks passing

5. **Plan Resolution**
   - If mitigation succeeds: plan permanent fix (Phase 5)
   - If partial improvement: evaluate additional mitigations
   - If unsuccessful: try alternate mitigation approach

6. **Continuous Communication**
   - Update status page with progress
   - Notify stakeholders of expected resolution time
   - Example: "Mitigation applied. Monitoring for stability. Expected full resolution in 30 minutes."

**Decision Gate**: Once metrics stabilize and error rate returns to baseline, move to Phase 5 (Resolution).

---

### Phase 5: Resolution (Starts when user impact eliminated)

**Goal**: Ensure incident does not recur

**Timeline**: 30 minutes to several hours after mitigation

**Procedures**:

1. **Permanent Fix Deployment**
   - If workaround was applied (feature disabled, temporary patch):
     - Develop proper fix with full testing
     - Deploy during maintenance window or with canary deployment
     - Gradually roll out to 25% → 50% → 100% of traffic
   - If temporary mitigation (rollback, scaling):
     - Analyze root cause
     - Develop permanent fix
     - Schedule deployment for next release cycle

2. **Post-Mitigation Verification**
   - Monitor metrics for 30+ minutes post-deployment
   - Run smoke tests on critical workflows
   - Verify no new issues introduced
   - Check logs for any warnings or anomalies

3. **Stakeholder Notification**
   - Send resolution update to status page
   - Notify customers via email/announcement
   - Update incident ticket with final status
   - Release follow-up communication

4. **Documentation**
   - Create follow-up ticket for post-mortem
   - Tag ticket with "incident" and severity level
   - Reference incident ID and relevant runbook
   - Estimate timeline for post-mortem (within 48 hours)

5. **Knowledge Transfer**
   - Share incident summary with broader team
   - Update runbooks if new discovery
   - Add monitoring/alerting if lacking
   - Identify training needs

**Decision Gate**: Declare incident resolved once:
- User impact eliminated
- Metrics stable for 30+ minutes
- Permanent fix scheduled or deployed
- All notifications sent

---

### Phase 6: Post-Incident (Within 48 hours)

**Goal**: Learn from incident and prevent recurrence

**Timeline**: Post-incident review within 48 hours

**Procedures**:

1. **Organize Post-Mortem Meeting**
   - Include: IC, Lead Investigator, Communications Lead, relevant SMEs
   - Schedule for within 24-48 hours of resolution
   - Allow 60-90 minutes for discussion
   - Include optional stakeholder debrief

2. **Complete Post-Mortem Document** (template provided below)
   - Document timeline of events
   - Identify root cause(s)
   - Determine contributing factors
   - Propose preventive actions

3. **Action Item Tracking**
   - Create tickets for preventive actions
   - Assign owners and target completion dates
   - Prioritize based on impact and effort
   - Link tickets to incident

4. **Metrics & Reporting**
   - Calculate MTTR (Mean Time To Repair)
   - Calculate MTTD (Mean Time To Detect)
   - Assess SLA compliance
   - Report to leadership if significant incident

5. **Team Communication**
   - Share post-mortem with team and stakeholders
   - Discuss learnings in team meeting
   - Highlight "well done" aspects
   - Prevent blame culture

---

## Communication Templates

### Template 1: Initial Update (5-10 minutes)

**Channel**: Status Page + Slack (#general or customer channel) + Email (for P1)

**Timeline**: Within 5-10 minutes of detecting incident

```
Subject: [INVESTIGATING] 88i Sinistro API - Investigating Service Degradation

We have detected issues affecting the 88i Sinistro API and are actively investigating.

IMPACT:
- Service: API Request Processing
- Status: Degraded - Increased error rates detected
- User Impact: Some API requests may fail or experience delays

WHAT WE'RE DOING:
- Investigating error logs and metrics
- Checking database connectivity and performance
- Reviewing recent deployments

NEXT UPDATE:
We will provide an update within 10 minutes with more details.

Incident ID: INC-2024-05-27-001
Status Page: https://status.88i-sinistro.io
```

### Template 2: Progress Update (30-minute intervals)

**Channel**: Status Page + Slack (#incident channel) + Email (for P1/P2)

**Timeline**: Every 15-30 minutes during active incident

```
Subject: [UPDATE] 88i Sinistro API - Incident Update - 30min into incident

CURRENT STATUS:
- Error rate has decreased from 12% to 6% - partial improvement
- Root cause identified: Database query performance degradation
- Mitigation in progress

ROOT CAUSE:
A recent deployment introduced a N+1 query pattern affecting the user-lookup endpoint. 
This is causing excessive database connections and query timeouts.

MITIGATION:
- Scaling application to 8 pods (from 4) to distribute load
- Disabling the affected feature via feature flag as workaround
- Preparing code rollback as backup plan

ESTIMATED RESOLUTION:
- Expected full resolution: 15-20 minutes from now
- Monitoring metrics closely during mitigation

NEXT UPDATE:
5-10 minutes

Incident ID: INC-2024-05-27-001
War Room: [Zoom Link]
```

### Template 3: Resolution Update

**Channel**: Status Page + Slack + Email + Customer Announcement

**Timeline**: Immediately upon resolution (typically 30-120 minutes after detection)

```
Subject: [RESOLVED] 88i Sinistro API - Service Restored

RESOLUTION:
The 88i Sinistro API service has been fully restored to normal operation.

ROOT CAUSE:
A recent deployment (v2.4.5) introduced a database query optimization issue in 
the user-lookup endpoint, causing connection pool exhaustion.

RESOLUTION STEPS TAKEN:
1. Disabled the affected feature via feature flag (5 min)
2. Scaled application instances from 4 to 8 pods (10 min)
3. Performed database connection cleanup (5 min)
4. Verified all metrics returned to baseline
5. Deployed code fix and verified in staging

IMPACT SUMMARY:
- Duration: 45 minutes
- Affected Users: ~2,500 (3% of active users)
- Peak Error Rate: 12%
- Peak Latency: 850ms P95

POST-INCIDENT:
- Post-mortem scheduled for [Date/Time]
- Code fix (commit XYZ) will be included in next release
- Monitoring improvements planned to catch similar issues faster

We apologize for the disruption and appreciate your patience. 
A detailed incident report will be published within 24 hours.

Incident ID: INC-2024-05-27-001
Status Page: https://status.88i-sinistro.io
```

---

## Post-Mortem Template

### Post-Incident Review Document

**Incident ID**: INC-2024-05-27-001  
**Date**: May 27, 2024  
**Duration**: 45 minutes (09:15 - 10:00 UTC)  
**Severity**: P2 (High)  

#### Executive Summary

On May 27, 2024 at 09:15 UTC, the 88i Sinistro API experienced elevated error rates 
(peak 12%) due to a database query optimization issue introduced in deployment v2.4.5. 
The issue affected approximately 3% of active users (2,500 users) and was resolved in 
45 minutes. The incident was caused by a missing database index on a frequently-queried 
field, which was exacerbated by a code change that introduced a N+1 query pattern.

#### Timeline

| Time | Event | Action |
|------|-------|--------|
| 09:15 | Alert fires: Error rate >5% | On-call engineer paged |
| 09:18 | Incident declared, war room opened | Lead investigator reviews logs |
| 09:22 | Root cause identified: DB query issue | Decision to disable feature via flag |
| 09:23 | Feature flag deployment | Feature disabled; error rate drops to 6% |
| 09:28 | Partial mitigation successful; scaling initiated | Application scaled to 8 pods |
| 09:33 | Database cleanup performed | Terminated idle connections |
| 09:38 | All metrics return to baseline | Service declared stable |
| 09:40 | Code rollback deployed as backup | v2.4.4 reverted |
| 09:45 | Resolution confirmed; war room closed | Post-mortem scheduled |
| 10:00 | Post-incident summary published | Stakeholders notified |

#### Root Cause Analysis

**Primary Cause**: N+1 Query Pattern in User-Lookup Endpoint
- Deployment v2.4.5 introduced code that queries user table once per result in a list operation
- For a request returning 100 users, this resulted in 100+ database queries instead of 1
- Database connection pool became exhausted, causing cascading timeouts

**Contributing Factors**:
1. Missing database index on `users.org_id` field
   - Query should have completed in <5ms; took >500ms without index
2. No performance testing in staging
   - N+1 pattern was not caught during code review or testing
3. Feature was enabled for all users immediately
   - No canary deployment or gradual rollout
4. No circuit breaker on database connection pool
   - Allowed cascading failures once pool exhausted

#### Root Cause

The root cause was a code change in `/app/handlers/users.py` (lines 42-58) that 
was introduced to improve user experience by loading full user objects instead of 
summary. However, the implementation fetched users in a loop rather than using a 
batch query.

**Code Diff**:
```python
# Before (v2.4.4) - Correct
@app.get("/users")
def list_users():
    return db.query(User).filter(User.org_id == current_org).all()

# After (v2.4.5) - Problematic N+1
@app.get("/users")
def list_users():
    summaries = db.query(UserSummary).filter(UserSummary.org_id == current_org).all()
    users = []
    for summary in summaries:  # ← N+1 query pattern
        user = db.query(User).filter(User.id == summary.user_id).first()
        users.append(user)
    return users
```

#### Preventive Actions

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Add database index on `users.org_id` | DBA | Jun 1 | Assigned |
| Implement performance testing in CI/CD | Dev Lead | Jun 5 | Assigned |
| Add N+1 query detection to linter | Platform | Jun 10 | Assigned |
| Implement canary deployments | DevOps | Jun 15 | Assigned |
| Add circuit breaker to DB connection pool | Backend | Jun 20 | Assigned |
| Increase monitoring on query performance | Ops | Jun 1 | Assigned |

#### Follow-Up Items

1. **Code Review Process**: Add performance checklist to code review
2. **Testing**: Implement load testing in CI/CD pipeline
3. **Monitoring**: Add alert for P95 query latency >200ms
4. **Documentation**: Update RUNBOOKS.md with this scenario
5. **Training**: Conduct ORM best practices training for team

#### Lessons Learned

**What Went Well**:
- Alert triggered quickly (within 2 minutes)
- Team responded immediately and systematically
- Root cause identified within 7 minutes
- Feature flag allowed quick mitigation without code deployment
- Good communication with customers

**What Could Be Improved**:
- Code review should have caught N+1 pattern
- Staging environment should have realistic data volumes
- Canary deployment would have limited user impact
- Index should have existed before code change

**Action Items for Team**:
- Review all recent code changes for N+1 patterns
- Add performance requirements to ticket acceptance criteria
- Schedule quarterly ORM training sessions

---

## Post-Mortem Meeting Checklist

- [ ] Incident details documented (ID, duration, severity, impact)
- [ ] Timeline created with all major events
- [ ] Root cause clearly identified (not just symptoms)
- [ ] Contributing factors documented
- [ ] At least 3 preventive actions identified
- [ ] Action items assigned with owners and due dates
- [ ] Meeting notes published to team
- [ ] Follow-up metrics planned (if applicable)
- [ ] Blameless culture reinforced (focus on process, not people)
- [ ] Post-mortem shared with broader engineering organization
