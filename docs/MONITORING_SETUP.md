# 88i Sinistro Monitoring Setup Guide

This guide provides comprehensive instructions for setting up Prometheus, Grafana, and alerting for the 88i Sinistro production environment.

## Prerequisites

- Docker and Docker Compose installed
- 88i Sinistro service running on `localhost:8000` with `/metrics` endpoint
- Alertmanager for alert routing
- Grafana for visualization

---

## Prometheus Installation and Configuration

### Step 1: Start Prometheus with Docker

```bash
docker run -d \
  --name prometheus \
  --restart unless-stopped \
  -p 9090:9090 \
  -v $(pwd)/config/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/config/alert_rules.yml:/etc/prometheus/alert_rules.yml \
  -v prometheus_data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --storage.tsdb.retention.time=30d
```

### Configuration Details

The `prometheus.yml` configuration includes:

- **Global Settings:**
  - `scrape_interval: 15s` - Default scrape interval for all jobs
  - `evaluation_interval: 15s` - Interval for evaluating alert rules

- **Scrape Config (88i-sinistro):**
  - Target: `localhost:8000`
  - Metrics path: `/metrics`
  - Scrape interval: `10s` (override for faster collection)
  - External labels: `cluster: production`, `environment: railway`

- **Alert Configuration:**
  - Alertmanager endpoint: `localhost:9093`
  - Rule files: `alert_rules.yml`

### Verify Prometheus

```bash
curl http://localhost:9090/api/v1/targets
curl http://localhost:9090/api/v1/alerts
```

---

## Alertmanager Setup

### Start Alertmanager

```bash
docker run -d \
  --name alertmanager \
  --restart unless-stopped \
  -p 9093:9093 \
  -v $(pwd)/config/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml
```

Create `config/alertmanager.yml` with basic configuration:

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:8001/webhook'
```

---

## Grafana Setup

### Step 2: Start Grafana

```bash
docker run -d \
  --name grafana \
  --restart unless-stopped \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_INSTALL_PLUGINS=grafana-worldmap-panel \
  -v grafana_data:/var/lib/grafana \
  -v $(pwd)/config/grafana_dashboard.json:/etc/grafana/provisioning/dashboards/sinistro.json \
  grafana/grafana:latest
```

**Access Grafana:** http://localhost:3000 (username: `admin`, password: `admin`)

### Step 3: Configure Prometheus Data Source

1. Navigate to **Configuration → Data Sources**
2. Click **Add Data Source**
3. Select **Prometheus**
4. Configure:
   - Name: `Prometheus`
   - URL: `http://prometheus:9090`
   - Access: `Browser` (for local testing)
   - Click **Save & Test**

### Step 4: Import Dashboard

1. Navigate to **Dashboards → Import**
2. Upload or paste the content of `config/grafana_dashboard.json`
3. Select **Prometheus** as the data source
4. Click **Import**

The dashboard will be available at the URL shown after import.

---

## Alert Rules Configuration

Alert rules are defined in `config/alert_rules.yml` with the following categories:

### SLA Breach Alerts

**ExtractLatencySLABreach**
- Expression: `histogram_quantile(0.95, rate(extract_latency_seconds_bucket[5m])) > 0.1`
- Threshold: p95 latency > 100ms
- Duration: 5 minutes
- Severity: Warning

**FraudScoringLatencySLABreach**
- Expression: `histogram_quantile(0.95, rate(fraud_scoring_latency_seconds_bucket[5m])) > 0.15`
- Threshold: p95 latency > 150ms
- Duration: 5 minutes
- Severity: Warning

### Error Rate Alerts

**HighErrorRate**
- Expression: `rate(sinistro_requests_total{status=~"5.."}[5m]) > 0.05`
- Threshold: Error rate > 5%
- Duration: 5 minutes
- Severity: Critical

### Resource Alerts

**HighCPUUsage**
- Expression: `process_cpu_seconds_total > 0.8`
- Threshold: CPU usage > 80%
- Duration: 5 minutes
- Severity: Warning

**HighMemoryUsage**
- Expression: `process_resident_memory_bytes / 1024 / 1024 / 1024 > 0.8`
- Threshold: Memory usage > 80%
- Duration: 5 minutes
- Severity: Warning

### Service Health Alerts

**ServiceDown**
- Expression: `up{job="88i-sinistro"} == 0`
- Threshold: Service unavailable
- Duration: 1 minute
- Severity: Critical

---

## PagerDuty Integration

### Configure PagerDuty in Alertmanager

Update `config/alertmanager.yml`:

```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<YOUR_PAGERDUTY_SERVICE_KEY>'
        description: 'Sinistro Alert: {{ .GroupLabels.alertname }}'
        details:
          firing: '{{ range .Alerts.Firing }}{{ .Labels.instance }} - {{ .Annotations.summary }}\n{{ end }}'

route:
  receiver: 'pagerduty'
```

### Steps:

1. Create a PagerDuty account and service
2. Generate an integration key
3. Update the `service_key` in alertmanager configuration
4. Restart Alertmanager: `docker restart alertmanager`

---

## Email Notifications

### Configure Email in Alertmanager

Update `config/alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-app-password'
  smtp_require_tls: true

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@yourcompany.com'
        from: 'sinistro-alerts@yourcompany.com'
        headers:
          Subject: 'Sinistro Alert: {{ .GroupLabels.alertname }}'
```

### Gmail Setup:

1. Enable 2-factor authentication on your Gmail account
2. Generate an app-specific password
3. Use the app password in the `smtp_auth_password` field

---

## Dashboard Metrics Reference

The Grafana dashboard includes 7+ panels organized by category:

### Health Metrics

- **Request Rate**: Total requests per second across all endpoints
  - Query: `rate(sinistro_requests_total[5m])`
  - Unit: Requests/sec

- **Error Rate**: Percentage of 5xx errors
  - Query: `rate(sinistro_requests_total{status=~"5.."}[5m])`
  - Unit: Percentage

- **Service Status**: Up/down status of Sinistro service
  - Query: `up{job="88i-sinistro"}`
  - Unit: Boolean

### Performance Metrics

- **P95 Latency by Endpoint**: 95th percentile latency for each endpoint
  - Query: `histogram_quantile(0.95, rate(sinistro_request_duration_seconds_bucket[5m]))`
  - Unit: Seconds

- **Extract Latency SLA**: Extract operation p95 latency vs 100ms threshold
  - Query: `histogram_quantile(0.95, rate(extract_latency_seconds_bucket[5m]))`
  - Unit: Seconds

- **Fraud Scoring Latency SLA**: Fraud scoring p95 latency vs 150ms threshold
  - Query: `histogram_quantile(0.95, rate(fraud_scoring_latency_seconds_bucket[5m]))`
  - Unit: Seconds

### Resource Metrics

- **CPU Usage**: Process CPU time consumption rate
  - Query: `rate(process_cpu_seconds_total[5m])`
  - Unit: Percentage

- **Memory Usage**: Resident memory consumption
  - Query: `process_resident_memory_bytes / 1024 / 1024`
  - Unit: MB

- **File Descriptors**: Open file descriptor count
  - Query: `process_open_fds`
  - Unit: Count

### Business Metrics

- **Sinistro Processing Rate**: Items processed per second by operation
  - Query: `rate(sinistro_processed_items_total[5m])`
  - Unit: Operations/sec

- **Fraud Score Distribution**: Heatmap of fraud score ranges over time
  - Query: `rate(fraud_score_bucket[5m])`
  - Unit: Distribution

- **Extract Success Rate**: Percentage of successful extractions
  - Query: `rate(extract_success_total[5m]) / rate(extract_attempts_total[5m])`
  - Unit: Percentage

---

## Testing and Verification

### Verify Metric Collection

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Query a specific metric
curl 'http://localhost:9090/api/v1/query?query=up{job="88i-sinistro"}'

# Check alert rules
curl http://localhost:9090/api/v1/rules | jq '.data.groups[0].rules'
```

### Verify Alertmanager

```bash
# Check active alerts
curl http://localhost:9093/api/v1/alerts | jq '.data'

# Check alert groups
curl http://localhost:9093/api/v1/alerts/groups | jq '.data'
```

### Verify Grafana

1. Navigate to http://localhost:3000
2. Go to the 88i Sinistro Production dashboard
3. Verify panels are displaying data
4. Check for any data source errors

---

## Troubleshooting

### Prometheus not scraping metrics

- Check that 88i Sinistro is running on `localhost:8000`
- Verify `/metrics` endpoint is accessible: `curl http://localhost:8000/metrics`
- Check Prometheus logs: `docker logs prometheus`
- Verify `prometheus.yml` syntax: `docker exec prometheus promtool check config /etc/prometheus/prometheus.yml`

### Grafana dashboard empty

- Verify Prometheus data source is configured and working
- Check that metrics exist in Prometheus: `curl http://localhost:9090/api/v1/query?query=up`
- Verify time range is correct (at least 5 minutes of data)

### Alerts not firing

- Check alert rules syntax: `docker exec prometheus promtool check rules /etc/prometheus/alert_rules.yml`
- Verify alert expressions in Prometheus UI: http://localhost:9090/alerts
- Check Alertmanager logs: `docker logs alertmanager`
- Verify Alertmanager configuration: `docker exec alertmanager amtool config routes`

### No notifications received

- Test email SMTP settings separately
- Check Alertmanager logs for delivery errors
- Verify receiver configuration in `alertmanager.yml`
- Test webhook endpoint if using webhooks

---

## Production Recommendations

1. **Data Retention**: Increase `storage.tsdb.retention.time` to 30+ days for production
2. **High Availability**: Use Prometheus federation or remote storage for redundancy
3. **Backup**: Regularly backup Grafana configuration and Prometheus data
4. **Authentication**: Enable Grafana authentication and RBAC in production
5. **TLS**: Configure TLS for all communication between Prometheus, Grafana, and Alertmanager
6. **Scaling**: Use distributed setups for high-volume metrics collection
7. **SLA Monitoring**: Regularly review and adjust SLA thresholds based on business needs

---

## Support and Documentation

- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/
- **Alertmanager**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **PromQL**: https://prometheus.io/docs/prometheus/latest/querying/basics/

For 88i Sinistro specific metrics, refer to the application documentation.
