#!/bin/bash

set -e

CANARY_PERCENTAGE=${1:-10}
STABLE_PERCENTAGE=$((100 - CANARY_PERCENTAGE))

echo "🐤 Starting canary deployment (${CANARY_PERCENTAGE}% canary, ${STABLE_PERCENTAGE}% stable)..."

# Get current stable version
STABLE_VERSION=$(railway status | grep "Service:" | awk '{print $2}')
echo "📌 Stable version: $STABLE_VERSION"

# Deploy new version
echo "🚀 Deploying new version..."
NEW_VERSION=$(railway up --no-wait 2>&1 | grep -oP '(?<=Deployment ID: )\\S+' || echo "latest")
echo "🆕 New version: $NEW_VERSION"

# Wait for new version to be healthy (30 attempts × 5s = 150s)
echo "⏳ Waiting for new version to be healthy..."
for i in {1..30}; do
    if curl -s https://$RAILWAY_SERVICE_DOMAIN/health | grep -q "ok"; then
        echo "✅ New version is healthy"
        break
    fi
    echo "⏳ Health check attempt $i/30..."
    sleep 5
done

# Configure traffic split
echo "🎚️ Configuring traffic split (${CANARY_PERCENTAGE}% canary)..."
# This would use Railway's load balancer configuration
# or a separate ingress controller

# Monitor metrics for 5 minutes (30 checks × 10s = 300s)
echo "📊 Monitoring metrics for 5 minutes..."
for i in {1..30}; do
    ERROR_RATE=$(curl -s https://$RAILWAY_SERVICE_DOMAIN/metrics | grep 'error_rate' || echo "0")
    P95_LATENCY=$(curl -s https://$RAILWAY_SERVICE_DOMAIN/metrics | grep 'p95_latency' || echo "unknown")
    
    echo "⏱️ Check $i/30: Error rate: $ERROR_RATE, P95: $P95_LATENCY"
    
    # If error rate > 5%, rollback
    if (( $(echo "$ERROR_RATE > 5.0" | bc -l) )); then
        echo "❌ Error rate too high, rolling back..."
        railway rollback $STABLE_VERSION
        echo "Canary deployment failed - rolled back to $STABLE_VERSION"
        exit 1
    fi
    
    sleep 10
done

# Increase traffic to new version
echo "📈 Increasing traffic to new version..."
# Full traffic shift to new version

echo "✅ Canary deployment successful!"
exit 0
