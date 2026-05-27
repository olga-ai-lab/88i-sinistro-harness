#!/bin/bash

set -e

TARGET_VERSION=${1:-previous}

echo "🔄 Rolling back to $TARGET_VERSION..."

railway rollback $TARGET_VERSION

echo "⏳ Waiting for rollback to complete..."
sleep 10

# Verify rollback
if curl -s https://$RAILWAY_SERVICE_DOMAIN/health | grep -q "ok"; then
    echo "✅ Rollback successful"
    exit 0
else
    echo "❌ Rollback failed - health check failed"
    exit 1
fi
