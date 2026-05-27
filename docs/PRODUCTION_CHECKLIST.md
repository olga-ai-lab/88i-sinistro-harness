# Production Checklist & Launch Procedures

**Last Updated:** May 27, 2026
**Status:** Pre-Launch
**Lead:** DevOps Team

---

## Phase 1: Pre-Launch Week (7 Days Before Go-Live)

### Security Hardening

- [ ] **SSL/TLS Configuration**
  - [ ] Obtain valid SSL certificate from CA (not self-signed)
  - [ ] Verify certificate chain (DigiCert/Let's Encrypt/AWS ACM)
  - [ ] Test SSL/TLS 1.2+ enforcement
  - [ ] Configure HSTS header (Strict-Transport-Security: max-age=31536000)
  - [ ] Run SSL Labs test (target: A+ rating)

- [ ] **API Key & Secret Management**
  - [ ] Rotate all production API keys (GitHub, Stripe, AWS, etc.)
  - [ ] Store secrets in AWS Secrets Manager / HashiCorp Vault
  - [ ] Verify no API keys in code/Git history
  - [ ] Implement key rotation schedule (90 days)
  - [ ] Configure API key rate limiting (CloudFlare/AWS WAF)

- [ ] **Encryption at Rest & in Transit**
  - [ ] Enable database encryption (RDS, PostgreSQL, etc.)
  - [ ] Configure TLS for database connections (SSL mode: require)
  - [ ] Verify all inter-service communication encrypted
  - [ ] Test encryption key rotation procedures
  - [ ] Document encryption key escrow procedures

- [ ] **Backup & Disaster Recovery**
  - [ ] Enable automated database backups (daily + hourly snapshots)
  - [ ] Test backup restoration (full recovery test)
  - [ ] Verify backup encryption & access controls
  - [ ] Document backup retention policy (30 days min)
  - [ ] Configure cross-region replication if applicable

- [ ] **OWASP Top 10 Security Audit**
  - [ ] A01:2021 – Broken Access Control: Role-based access testing
  - [ ] A02:2021 – Cryptographic Failures: Encryption verification
  - [ ] A03:2021 – Injection: SQL injection / command injection tests
  - [ ] A04:2021 – Insecure Design: Security threat modeling
  - [ ] A05:2021 – Security Misconfiguration: Server hardening
  - [ ] A06:2021 – Vulnerable & Outdated Components: Dependency audit
  - [ ] A07:2021 – Authentication Failures: MFA, session management
  - [ ] A08:2021 – Software & Data Integrity: Code signing, artifact verification
  - [ ] A09:2021 – Logging & Monitoring Failures: Audit trail setup
  - [ ] A10:2021 – SSRF: External service request validation

### Performance Optimization

- [ ] **Load Testing**
  - [ ] Run sustained load test (100 concurrent users for 30 min)
  - [ ] Identify bottlenecks & response time distributions
  - [ ] Test graceful degradation under 2x peak load
  - [ ] Verify auto-scaling triggers correctly

- [ ] **SLA Validation**
  - [ ] Confirm 99.5% uptime target for all services
  - [ ] Set error budget thresholds (max 0.5% errors/hour)
  - [ ] Document response time SLAs (p99 < 500ms typical)
  - [ ] Configure alerts for SLA breaches

- [ ] **Caching Strategy**
  - [ ] Redis cache fully configured & tested
  - [ ] Cache invalidation logic verified
  - [ ] TTL values optimized for data freshness
  - [ ] Cache hit rates monitored (target: 80%+)

- [ ] **Database Indexes**
  - [ ] All critical queries have covering indexes
  - [ ] Query plans reviewed (no full table scans)
  - [ ] Index fragmentation checked (< 10% target)
  - [ ] Statistics updated

### Infrastructure & Scaling

- [ ] **Monitoring Setup**
  - [ ] CloudWatch / Datadog metrics configured
  - [ ] Application performance monitoring (APM) enabled
  - [ ] Custom business metrics exported
  - [ ] Distributed tracing (X-Ray / Jaeger) operational

- [ ] **Alerting & Escalation**
  - [ ] PagerDuty / Alertmanager fully configured
  - [ ] Critical alerts → on-call immediately
  - [ ] Warning alerts → aggregated & reviewed hourly
  - [ ] Alert fatigue mitigation (grouping, suppression rules)
  - [ ] Escalation chains defined per severity

- [ ] **Health Checks & Readiness**
  - [ ] `/health` endpoint returns 200 OK
  - [ ] `/ready` endpoint validates all dependencies
  - [ ] Kubernetes liveness/readiness probes configured
  - [ ] Health check frequency: every 10 seconds
  - [ ] Timeout: 5 seconds max

- [ ] **Auto-Scaling**
  - [ ] Horizontal scaling configured (min 3, max 20 instances)
  - [ ] Scaling policies tested (scale up/down)
  - [ ] Graceful shutdown (30 sec drain) implemented
  - [ ] Connection draining verified

### Reliability & Disaster Recovery

- [ ] **Disaster Recovery Testing**
  - [ ] Simulate single AZ failure (verify failover < 60s)
  - [ ] Simulate database failover (RDS multi-AZ)
  - [ ] Simulate complete region failure (if multi-region)
  - [ ] Document recovery procedures & RTO/RPO

- [ ] **Data Integrity Checks**
  - [ ] Run database consistency checks
  - [ ] Verify foreign key constraints
  - [ ] Test data migration rollback procedures
  - [ ] Backup validation automated

- [ ] **Failover Testing**
  - [ ] DNS failover tested (CNAME/Route53 records)
  - [ ] Load balancer failover verified
  - [ ] Database primary/replica failover tested
  - [ ] Cache failover (Redis Sentinel/Cluster) operational

- [ ] **Incident Playbooks**
  - [ ] Database connection pool exhaustion
  - [ ] API response time degradation
  - [ ] High error rate response
  - [ ] DDoS attack mitigation
  - [ ] Data corruption / integrity breach
  - [ ] Security incident response
  - [ ] Storage capacity exceeded

### Operational Readiness

- [ ] **Runbooks Created**
  - [ ] Common incident response procedures
  - [ ] Deployment rollback procedures
  - [ ] Emergency scaling procedures
  - [ ] Database backup/restore procedures
  - [ ] Troubleshooting guide

- [ ] **Status Page**
  - [ ] Public status page configured (Statuspage.io / Atlassian)
  - [ ] Real-time incident updates enabled
  - [ ] Historical uptime data displayed
  - [ ] Subscriber notifications configured

- [ ] **Communication Templates**
  - [ ] Incident declaration template
  - [ ] Customer notification email template
  - [ ] Post-incident review (PIR) template
  - [ ] Deployment notification template

- [ ] **Team Training & Documentation**
  - [ ] All ops team members trained on runbooks
  - [ ] On-call rotation established
  - [ ] Escalation procedures documented
  - [ ] Architecture diagram updated
  - [ ] API documentation complete
  - [ ] Database schema documented

---

## Phase 2: Launch Day

### Pre-Launch Verification (T-60 Minutes)

- [ ] System health check: `scripts/final_security_check.sh`
  - [ ] All security checks passing ✅
  - [ ] No HIGH/CRITICAL vulnerabilities
  - [ ] Secrets scanning clean
  - [ ] SSL certificate valid (> 30 days)
  - [ ] Database connectivity confirmed

- [ ] Performance baseline: `scripts/final_performance_check.sh <domain>`
  - [ ] Health check responding
  - [ ] Extract endpoint latency: < 500ms p99
  - [ ] Fraud detection latency: < 1000ms p99
  - [ ] 10 concurrent requests without errors
  - [ ] Performance metrics endpoint responding

- [ ] Infrastructure readiness
  - [ ] All instances/pods healthy and running
  - [ ] Load balancer routing traffic correctly
  - [ ] Cache (Redis) operational
  - [ ] Database primary/replica in sync
  - [ ] Monitoring & logging systems active

- [ ] Team readiness
  - [ ] On-call engineer online & alert-ready
  - [ ] Incident commander assigned
  - [ ] Status page staging tested
  - [ ] Communication channels (Slack, PagerDuty) open

### Launch Steps (T=0)

Execute in order. Each command should complete with exit code 0.

```bash
# Step 1: Verify production environment loaded
export ENV=production
echo "Environment: $ENV"

# Step 2: Run final security scan
bash /path/to/scripts/final_security_check.sh

# Step 3: Run final performance check against staging
bash /path/to/scripts/final_performance_check.sh https://staging-api.example.com

# Step 4: DNS cutover (if applicable) - single shot, no rollback
# Verify DNS propagation:
dig +short api.example.com

# Step 5: Enable production traffic (set load balancer weight to 100%)
# AWS ALB: update target group attributes
# kubectl: scale production deployment, update ingress

# Step 6: Post-launch verification (run in 60 seconds)
bash /path/to/scripts/final_performance_check.sh https://api.example.com
```

### Post-Launch Hour 1: Critical Metrics Targets

Monitor continuously. Alert on any breach.

- [ ] **Availability**: 99.9% (max 3.6 seconds downtime)
- [ ] **Error Rate**: < 0.5% (p95)
- [ ] **Response Time**:
  - [ ] Extract endpoint: p99 < 500ms
  - [ ] Fraud detection: p99 < 1000ms
  - [ ] Health check: p99 < 100ms
- [ ] **Throughput**: >= baseline (load test performance)
- [ ] **Database Connections**: < 80% pool capacity
- [ ] **Cache Hit Rate**: > 70%
- [ ] **CPU**: < 70%
- [ ] **Memory**: < 80%
- [ ] **Disk**: < 85%

**Action**: If ANY metric breaches → immediate incident call → determine cause → implement fix or rollback.

### Post-Launch Day 1: Extended Metrics Targets

Aggregate over 24 hours.

- [ ] **Availability**: 99.5% (< 432 seconds downtime)
- [ ] **Error Rate**: < 1% (p95)
- [ ] **Response Time** (p99): Extract < 600ms, Fraud < 1200ms
- [ ] **P99 Latency**: No spike > 2x baseline
- [ ] **Successful Transactions**: >= 95% (retry-exempt)
- [ ] **User Feedback**: No critical complaints in support channel
- [ ] **Incident Count**: 0 (post-launch hour 1) or resolved < 30 min each
- [ ] **Cost/Request**: Within budget
- [ ] **Data Consistency**: Zero integrity issues logged

---

## Phase 3: Post-Launch Week (Days 2-7)

### Performance Analysis

- [ ] **Latency Deep Dive**
  - [ ] Analyze p50, p95, p99 distributions
  - [ ] Identify slow endpoints (> 2x baseline)
  - [ ] Database query performance review
  - [ ] Network latency attribution

- [ ] **Throughput Review**
  - [ ] Peak load handling (compare to load test)
  - [ ] Identify capacity limits
  - [ ] Check for unexpected traffic patterns
  - [ ] Validate SLA compliance

- [ ] **Resource Utilization**
  - [ ] CPU/Memory/Disk trends
  - [ ] Identify optimization opportunities
  - [ ] Right-size compute resources
  - [ ] Plan capacity for next 30 days

### Security Review

- [ ] **Post-Launch Security Audit**
  - [ ] Review access logs for anomalies
  - [ ] Verify no unauthorized API calls
  - [ ] Audit configuration changes
  - [ ] Check for data exfiltration attempts

- [ ] **Compliance & Auditing**
  - [ ] Log retention verified
  - [ ] Audit trails complete
  - [ ] Regulatory requirements (GDPR/HIPAA) met
  - [ ] Data classification reviewed

- [ ] **Vulnerability Management**
  - [ ] Rerun Trivy / dependency scan
  - [ ] Review CVE advisories
  - [ ] Patch critical issues immediately
  - [ ] Plan updates for medium/low priority

### Operational Review

- [ ] **Incident Retrospectives**
  - [ ] Document all incidents (even minor)
  - [ ] Root cause analysis (5 whys)
  - [ ] Preventive measures assigned
  - [ ] Tickets created for improvements

- [ ] **Runbook Updates**
  - [ ] Refine procedures based on actual incidents
  - [ ] Add new incident scenarios
  - [ ] Update alert thresholds if needed
  - [ ] Cross-train backup on-call

- [ ] **Cost Optimization**
  - [ ] Review cloud provider billing
  - [ ] Identify underutilized resources
  - [ ] Plan reserved instances / commitments
  - [ ] Optimize network costs

---

## Go-Live Sign-Off

**All stakeholders must sign off before proceeding.**

### Sign-Off Checklist

| Role | Name | Date | Signature | Status |
|------|------|------|-----------|--------|
| **Development Lead** | _ | _ | _ | ☐ Approved |
| **DevOps Lead** | _ | _ | _ | ☐ Approved |
| **Security Officer** | _ | _ | _ | ☐ Approved |
| **Product Manager** | _ | _ | _ | ☐ Approved |
| **Operations Manager** | _ | _ | _ | ☐ Approved |
| **CTO / Exec Sponsor** | _ | _ | _ | ☐ Approved |

### Final Approval

- [ ] **Development**: All features complete, tested, code reviewed
- [ ] **DevOps**: Infrastructure healthy, monitoring active, runbooks ready
- [ ] **Security**: No critical vulnerabilities, secrets secured, audit passed
- [ ] **Product**: Requirements met, user experience validated, go/no-go decision
- [ ] **Operations**: Team trained, on-call assigned, playbooks operational
- [ ] **Executive**: Business case validated, risk acceptable, decision made

**Go-Live Authorized By (CTO/Executive)**: ______________________  
**Date/Time**: ______________________  
**Incident Commander On Duty**: ______________________  
**Status Page Link**: ______________________  

---

## Post-Launch Communication

**Public Announcement Template:**

```
Subject: [SERVICE_NAME] Now Available

Dear Customers,

We're excited to announce that [SERVICE_NAME] is now generally available!

Features:
- [Feature 1]
- [Feature 2]
- [Feature 3]

Performance SLA: 99.5% uptime, < 500ms p99 latency
Support: support@example.com | status.example.com

Thank you for your patience!
```

**Internal Incident Declaration Template:**

```
INCIDENT DECLARED

Service: [SERVICE]
Severity: [CRITICAL/HIGH/MEDIUM/LOW]
Start Time: [UTC]
Status: [INVESTIGATING/MITIGATING/RESOLVED]

Description: [2-3 sentences]
Impact: [# customers affected, business impact]
Cause: [if known]
Mitigation: [steps in progress]
ETA Resolution: [estimate]

Next Update: [+15 min]
Incident Commander: [name]
```

---

## Monitoring & Alerts (Post-Launch)

### Key Performance Indicators (KPIs)

```
Extract API:
  ✓ p50 < 200ms
  ✓ p95 < 400ms
  ✓ p99 < 500ms
  ✓ Error Rate < 0.5%
  ✓ Availability 99.5%+

Fraud Detection API:
  ✓ p50 < 500ms
  ✓ p95 < 800ms
  ✓ p99 < 1000ms
  ✓ Error Rate < 1%

System Health:
  ✓ CPU: 30-70% (healthy range)
  ✓ Memory: 40-80%
  ✓ Disk: < 85%
  ✓ DB Connections: < 80% pool
```

### Alert Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Error Rate | > 1% (5 min avg) | Page on-call immediately |
| Latency p99 | > 1.5s | Page on-call, investigate |
| Availability | < 99% (1 hour) | Incident call |
| CPU | > 85% (5 min) | Auto-scale & page on-call |
| Memory | > 90% | Page on-call |
| Disk | > 90% | Page on-call immediately |

---

## Rollback Plan (If Critical Issues)

**Rollback Window:** T+30 minutes (automatic if not explicitly approved)

Steps:
1. Declare incident (all stakeholders notified)
2. Disable production traffic to new version
3. Route all traffic back to previous stable release
4. Verify system stability (5 min observation)
5. Root cause analysis & fix
6. Re-test before next deployment

**Do NOT rollback if:**
- Issue is data-related (corruption already present)
- Rollback would disconnect users mid-transaction
- Fix is < 5 minutes away

---

**Last reviewed:** May 27, 2026  
**Next review:** 7 days post-launch
