# Disaster Recovery & Data Integrity Guide

## Overview

This document outlines the disaster recovery (DR) strategy for the 88i Sinistro Harness system, including backup procedures, failover mechanisms, data recovery processes, and integrity verification. The goal is to minimize data loss (RPO) and service downtime (RTO) while ensuring data consistency and availability.

---

## Recovery Time & Recovery Point Objectives (RTO/RPO)

The following table defines the acceptable recovery objectives for different failure scenarios:

| Component | RTO (Recovery Time Objective) | RPO (Recovery Point Objective) | Notes |
|-----------|------------------------------|--------------------------------|-------|
| Database | 5 minutes | 1 hour | Primary DB recovery via failover; acceptable 1-hour data loss |
| Application | 1 minute | N/A | Stateless; rapid restart on secondary instance |
| Data Corruption | 1 hour | Same | Detect and restore from clean backup |
| Complete System | 30 minutes | 1 hour | Full infrastructure failover |

**Key Definitions:**
- **RTO:** Maximum acceptable downtime before service is restored
- **RPO:** Maximum acceptable data loss (time since last backup)

---

## Backup Strategy

### Backup Frequency

- **Hourly incremental backups** of the primary database
- **Daily full backups** for long-term retention
- **On-demand backups** before major operations

### Backup Retention Policy

- **Hot backups:** Last 7 days (stored locally or on fast storage)
- **Warm backups:** Previous 30 days (stored on S3)
- **Archive backups:** Previous 90 days (stored on Glacier or equivalent cold storage)

### Backup Storage

**Primary Storage Location:** S3 bucket with versioning enabled
- Bucket: `sinistro-harness-backups`
- Encryption: AES-256 at rest, TLS in transit
- Access: IAM role-based, MFA required for deletion

**Backup File Format:**
- **Database:** PostgreSQL pg_dump format (SQL plain text or custom format)
- **Application State:** JSON snapshots of critical configuration
- **Naming Convention:** `{component}_backup_{YYYYMMDD_HHMMSS}.{ext}`
  - Example: `postgres_backup_20260527_123456.sql`

### Daily Verification

Automated daily verification includes:

1. **File Integrity Check**
   - Verify backup file exists and is not corrupted
   - Validate file size is non-zero
   - Check MD5/SHA256 checksums

2. **Content Validation**
   - Verify SQL syntax in database backups
   - Validate JSON structure in configuration backups
   - Spot-check for expected tables and data

3. **Restorable Test** (weekly)
   - Restore backup to isolated test database
   - Run integrity checks on restored data
   - Verify data consistency with checksums

**Verification Script Location:** `scripts/verify_backups.sh`

```bash
#!/bin/bash
# Daily backup verification
0 2 * * * /opt/scripts/verify_backups.sh >> /var/log/backup_verification.log 2>&1
```

---

## Failover Procedures

### Database Failover

**Scenario:** Primary PostgreSQL instance fails or becomes unavailable

**Failover Script:** `scripts/database_failover.sh`

```bash
#!/bin/bash
set -euo pipefail

# Database Failover Script
# Switches traffic from primary to standby instance

PRIMARY_HOST="db-primary.internal"
STANDBY_HOST="db-standby.internal"
APP_CONFIG="/etc/app/database.conf"

# 1. Verify standby is ready
echo "[$(date)] Checking standby readiness..."
if ! pg_isready -h "$STANDBY_HOST" -p 5432; then
    echo "ERROR: Standby database not ready"
    exit 1
fi

# 2. Check replication lag
echo "[$(date)] Checking replication lag..."
LAG=$(psql -h "$STANDBY_HOST" -U postgres -c \
    "SELECT EXTRACT(EPOCH FROM (NOW() - pg_last_xact_replay_time()))" \
    -t -A)
if [ "$LAG" -gt 60 ]; then
    echo "WARNING: Replication lag is ${LAG}s, proceeding with failover"
fi

# 3. Promote standby
echo "[$(date)] Promoting standby database..."
psql -h "$STANDBY_HOST" -U postgres -c "SELECT pg_promote();"

# 4. Wait for promotion to complete
echo "[$(date)] Waiting for promotion to complete..."
sleep 10
if ! pg_isready -h "$STANDBY_HOST" -p 5432; then
    echo "ERROR: Promoted database not ready"
    exit 1
fi

# 5. Update application configuration
echo "[$(date)] Updating application configuration..."
sed -i "s/host=.*/host=$STANDBY_HOST/" "$APP_CONFIG"

# 6. Restart application services
echo "[$(date)] Restarting application services..."
systemctl restart app-service

# 7. Verify connectivity
echo "[$(date)] Verifying connectivity..."
sleep 5
curl -f http://localhost:8080/health || {
    echo "ERROR: Health check failed after failover"
    exit 1
}

echo "[$(date)] Database failover completed successfully"
```

**Failover Steps:**

1. Monitor detects primary database unavailability
2. Verify standby replica is caught up (replication lag < 1 minute)
3. Promote standby to primary role using `pg_promote()`
4. Update application configuration with new primary host
5. Perform health checks on new primary
6. Restart application services to refresh connections
7. Log and alert operations team

**Recovery Time:** ~2-3 minutes

### Application Failover

**Scenario:** Primary application instance fails or becomes unresponsive

**Failover Script:** `scripts/app_failover.sh`

```bash
#!/bin/bash
set -euo pipefail

# Application Failover Script
# Redirects traffic to standby application instance

PRIMARY_APP="app-primary.internal:8080"
STANDBY_APP="app-standby.internal:8080"
LB_CONFIG="/etc/load_balancer/backends.conf"
HEALTH_CHECK_RETRIES=5

# 1. Verify standby application is healthy
echo "[$(date)] Checking standby application health..."
for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
    if curl -f -s http://"$STANDBY_APP"/health >/dev/null; then
        echo "Standby application is healthy"
        break
    fi
    if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
        echo "ERROR: Standby application not healthy after $HEALTH_CHECK_RETRIES attempts"
        exit 1
    fi
    sleep 2
done

# 2. Mark primary as unhealthy in load balancer
echo "[$(date)] Marking primary application as unhealthy..."
sed -i "s/${PRIMARY_APP}.*server ${PRIMARY_APP} down/" "$LB_CONFIG"

# 3. Update load balancer configuration
echo "[$(date)] Reloading load balancer configuration..."
systemctl reload load-balancer

# 4. Verify traffic is flowing to standby
echo "[$(date)] Verifying traffic routing..."
sleep 3
ACTIVE_BACKENDS=$(curl -s http://load-balancer:8404/stats | grep -c "app-standby")
if [ "$ACTIVE_BACKENDS" -eq 0 ]; then
    echo "WARNING: No traffic detected on standby backend"
fi

# 5. Alert and log
echo "[$(date)] Application failover completed"
curl -X POST http://alerting:8080/alert \
    -d '{"severity": "critical", "message": "App failover executed: primary to standby"}'

echo "[$(date)] Application failover completed successfully"
```

**Failover Steps:**

1. Health checks detect primary application unavailability
2. Verify standby application health
3. Update load balancer configuration to remove primary
4. Route all traffic to standby instance
5. Perform end-to-end application health checks
6. Alert operations team
7. Investigate primary for restart

**Recovery Time:** ~30-60 seconds

---

## Data Recovery

### Recovery from Backup

**Scenario:** Need to restore data from a specific point in time

**Procedure:**

1. **List Available Backups**
   ```bash
   aws s3 ls s3://sinistro-harness-backups/ --recursive
   ```

2. **Verify Backup Integrity**
   ```python
   from app.backup import BackupManager
   
   manager = BackupManager(
       db_host="localhost",
       db_port=5432,
       db_user="postgres",
       db_name="sinistro_harness",
       backup_dir="/backups"
   )
   
   result = manager.verify_backup("/backups/postgres_backup_20260527_120000.sql")
   assert result["status"] == "ok", f"Backup verification failed: {result}"
   ```

3. **Restore from Backup**
   ```python
   import asyncio
   
   async def restore():
       result = await manager.restore_from_backup(
           backup_file="/backups/postgres_backup_20260527_120000.sql",
           target_db="sinistro_harness_restored"
       )
       assert result["status"] == "success", f"Restore failed: {result}"
       print(f"Restored to {result['database']} at {result['timestamp']}")
   
   asyncio.run(restore())
   ```

4. **Verify Restored Data**
   ```python
   from app.integrity import IntegrityChecker
   
   checker = IntegrityChecker("postgresql://localhost/sinistro_harness_restored")
   
   # Check consistency
   consistency = await checker.check_database_consistency()
   assert consistency["overall_status"] != "error"
   
   # Verify checksums
   checksum = await checker.verify_data_checksums("users")
   print(f"Restored data checksum: {checksum['checksum']}")
   ```

5. **Failover to Restored Database** (if primary is corrupt)
   - Update application configuration to use restored database
   - Run smoke tests
   - Cut over traffic to restored database

**Estimated Time:** 15-30 minutes (depending on database size)

### Point-in-Time Recovery (PITR)

**Scenario:** Restore database to a specific point in time

**Prerequisites:**
- WAL (Write-Ahead Log) archiving enabled on primary
- WAL files retained in S3 (minimum 30 days)

**Procedure:**

1. **Set Up Recovery Parameters**
   ```sql
   -- Create recovery.conf or postgresql.conf settings
   recovery_target_timeline = 'latest'
   recovery_target_time = '2026-05-27 12:00:00 UTC'
   restore_command = 'aws s3 cp s3://sinistro-harness-wal/%f %p'
   ```

2. **Initiate PITR Restore**
   ```bash
   # 1. Stop the database cluster
   systemctl stop postgresql
   
   # 2. Backup current data directory
   cp -r /var/lib/postgresql/main /var/lib/postgresql/main.backup
   
   # 3. Restore base backup from S3
   aws s3 cp s3://sinistro-harness-backups/base_backup.tar.gz - | \
       tar xzf - -C /var/lib/postgresql/main
   
   # 4. Place recovery.conf in data directory
   cp /etc/postgresql/recovery.conf /var/lib/postgresql/main/
   
   # 5. Start PostgreSQL (will perform PITR)
   systemctl start postgresql
   
   # 6. Monitor recovery progress
   tail -f /var/log/postgresql/postgresql.log | grep recovery
   ```

3. **Verify Recovered Data**
   - Connect to database
   - Run integrity checks
   - Compare with backups of known good state

**Estimated Time:** 30-60 minutes (depending on database size and WAL volume)

---

## Data Integrity Verification

### Automated Integrity Checks

The `IntegrityChecker` class performs continuous monitoring:

```python
from app.integrity import IntegrityChecker

checker = IntegrityChecker("postgresql://localhost/sinistro_harness")

# Check overall consistency
consistency = await checker.check_database_consistency()
print(f"Consistency status: {consistency['overall_status']}")
for check_name, result in consistency['checks'].items():
    print(f"  {check_name}: {result['status']} - {result['message']}")

# Verify specific table checksums
checksum = await checker.verify_data_checksums("critical_table")
print(f"Table checksum: {checksum['checksum']}")
```

**Checks Performed:**

1. **Orphaned Records** - Detect referential integrity violations
2. **Missing Indexes** - Identify missing or invalid indexes
3. **Table Bloat** - Monitor wasted space due to updates/deletes
4. **Connection Health** - Verify database connectivity and resource usage

### Manual Integrity Checks

```bash
# Check database size and usage
psql -U postgres -d sinistro_harness -c "
    SELECT 
        schemaname,
        SUM(pg_total_relation_size(schemaname||'.'||tablename)) as size_bytes
    FROM pg_tables
    GROUP BY schemaname
    ORDER BY size_bytes DESC;"

# Check table bloat
psql -U postgres -d sinistro_harness -c "
    SELECT 
        schemaname, 
        tablename, 
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
        round(100 * pg_total_relation_size(schemaname||'.'||tablename) / 
              pg_database_size('sinistro_harness'))::numeric(4,1) as pct
    FROM pg_tables
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check index health
psql -U postgres -d sinistro_harness -c "
    SELECT 
        schemaname,
        tablename,
        indexname,
        idx_scan as index_scans
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
    ORDER BY tablename;"
```

---

## Testing & Drills

### Monthly Disaster Recovery Drills

**Frequency:** First Tuesday of every month at 14:00 UTC

**Duration:** 1-2 hours

### Drill Checklist

- [ ] **Pre-Drill Setup** (30 minutes before)
  - [ ] Notify stakeholders and schedule maintenance window
  - [ ] Backup current production data
  - [ ] Take snapshot of current metrics/dashboards
  - [ ] Prepare test environment

- [ ] **Backup Testing**
  - [ ] Create on-demand backup of production database
  - [ ] Verify backup file integrity
  - [ ] Confirm backup is readable and has expected size
  - [ ] Validate SQL syntax of backup

- [ ] **Restoration Testing**
  - [ ] Restore backup to isolated test database
  - [ ] Verify schema matches production
  - [ ] Run automated integrity checks on restored data
  - [ ] Spot-check critical tables and records
  - [ ] Document restoration time

- [ ] **Application Failover Testing**
  - [ ] Simulate primary app failure (kill process or disable network)
  - [ ] Verify load balancer detects failure and routes to standby
  - [ ] Confirm application remains responsive to requests
  - [ ] Verify all endpoints remain functional
  - [ ] Check error logs for unexpected issues
  - [ ] Measure failover time from detection to recovery

- [ ] **Database Failover Testing**
  - [ ] Simulate primary database failure
  - [ ] Verify standby promotion occurs
  - [ ] Check replication lag before and after promotion
  - [ ] Confirm application reconnects to new primary
  - [ ] Run integrity checks on new primary
  - [ ] Document failover time

- [ ] **Data Integrity Testing**
  - [ ] Run `check_database_consistency()` on production
  - [ ] Run `verify_data_checksums()` on critical tables
  - [ ] Compare checksums between backup and restored data
  - [ ] Verify no orphaned records detected
  - [ ] Check for any missing indexes

- [ ] **Full System Recovery** (if time permits)
  - [ ] Perform complete failover to secondary datacenter
  - [ ] Run full smoke test suite
  - [ ] Verify metrics and monitoring on secondary
  - [ ] Test backup restoration from secondary site

- [ ] **Post-Drill Documentation**
  - [ ] Record actual RTO and RPO achieved
  - [ ] Document any issues encountered
  - [ ] Identify improvements or gaps
  - [ ] Update runbooks based on lessons learned
  - [ ] Notify stakeholders of results

### Drill Report Template

```markdown
## Disaster Recovery Drill Report - [DATE]

**Drill Type:** [Backup/Failover/Full System]
**Duration:** [HH:MM - HH:MM UTC]
**Participants:** [List of team members]

### Results

| Objective | Target | Actual | Status |
|-----------|--------|--------|--------|
| Backup Creation | 5 min | [X] min | [PASS/FAIL] |
| Backup Verification | 5 min | [X] min | [PASS/FAIL] |
| Data Restoration | 15 min | [X] min | [PASS/FAIL] |
| Application Failover | 1 min | [X] sec | [PASS/FAIL] |
| Database Failover | 5 min | [X] min | [PASS/FAIL] |
| System Readiness | - | [OK/DEGRADED] | [PASS/FAIL] |

### Issues & Resolutions

- **Issue 1:** [Description]
  - **Root Cause:** [Analysis]
  - **Resolution:** [Action taken]
  - **Follow-up:** [Future prevention]

### Recommendations

1. [Improvement 1]
2. [Improvement 2]
3. [Improvement 3]

### Sign-Off

- [ ] Operations Team Lead
- [ ] Database Team Lead
- [ ] Application Team Lead
```

---

## Runbooks

### Emergency Contacts

| Role | Name | Phone | Email | Escalation |
|------|------|-------|-------|-----------|
| On-Call SRE | [Name] | [Phone] | [Email] | Manager |
| Database DBA | [Name] | [Phone] | [Email] | SRE Lead |
| App Lead | [Name] | [Phone] | [Email] | Engineering Manager |

### Incident Response Flow

```
Detection
   ↓
  Alert (email, Slack, PagerDuty)
   ↓
  Confirm Issue (health checks, manual verification)
   ↓
  Declare Incident Severity (P1/P2/P3)
   ↓
  Initiate Response (page on-call engineer)
   ↓
  [Execute appropriate failover procedure above]
   ↓
  Monitor and Verify Recovery
   ↓
  Post-Incident Review (after 24 hours)
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

- **Backup Success Rate:** % of scheduled backups completed successfully
- **Backup Verification:** % of backups passing integrity checks
- **Replication Lag:** Time delta between primary and standby writes
- **Data Consistency:** % of consistency checks passing
- **Recovery Test Success:** % of periodic recovery tests passing

### Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| Backup Failed | Any failure | Page on-call |
| Replication Lag > 5 min | Continuous 5+ min | Investigate standby |
| Consistency Check Failed | Any failure | Investigate immediately |
| Backup Verification Failed | 2 consecutive failures | Pause backups, investigate |

---

## References

- PostgreSQL Backup & Restore: https://www.postgresql.org/docs/current/backup.html
- PostgreSQL Streaming Replication: https://www.postgresql.org/docs/current/streaming-replication.html
- AWS S3 Backup Best Practices: https://docs.aws.amazon.com/AmazonS3/latest/userguide/disaster-recovery.html
- RPO/RTO Definition: https://en.wikipedia.org/wiki/Disaster_recovery#Recovery_time_objective

---

**Document Version:** 1.0
**Last Updated:** May 27, 2026
**Next Review:** June 27, 2026
