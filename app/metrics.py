"""Metrics collection for monitoring."""

import os
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'app_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Error metrics
error_count = Counter(
    'app_errors_total',
    'Total errors',
    ['error_type']
)

# Business metrics
sinistro_processed = Counter(
    'sinistro_processed_total',
    'Total sinistros processed',
    ['tipo', 'result']
)

fraud_score_histogram = Histogram(
    'fraud_score_distribution',
    'Fraud score distribution',
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
)

# System metrics
active_connections = Gauge(
    'app_active_connections',
    'Active connections'
)

uptime = Gauge(
    'app_uptime_seconds',
    'Application uptime'
)
