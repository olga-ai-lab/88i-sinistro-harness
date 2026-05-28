#!/bin/bash

# Railway Health Check Monitoring Script
# Use this after Railway deployment is complete
# Polls /health endpoint every 10 seconds until 200 OK or timeout

RAILWAY_URL="${1:-https://octa.railway.app}"
MAX_ATTEMPTS=${2:-60}

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                               ║"
echo "║                   🚀 RAILWAY HEALTH CHECK MONITOR 🚀                         ║"
echo "║                                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Railway URL: $RAILWAY_URL/health"
echo "Max attempts: $MAX_ATTEMPTS"
echo "Interval: 10 seconds"
echo "Started: $(date)"
echo ""

for i in $(seq 1 $MAX_ATTEMPTS); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/health" 2>&1)
  TIMESTAMP=$(date '+%H:%M:%S')
  
  if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "✅✅✅ SUCCESS AT ATTEMPT $i!"
    echo "[$TIMESTAMP] /health = 200 OK"
    echo ""
    echo "Response:"
    curl -s "$RAILWAY_URL/health"
    echo ""
    echo ""
    echo "🎉🎉🎉 OCTA IS LIVE ON RAILWAY!"
    echo ""
    exit 0
  else
    echo "[$TIMESTAMP] Attempt $i/$MAX_ATTEMPTS: HTTP $HTTP_CODE"
    if [ $i -lt $MAX_ATTEMPTS ]; then
      sleep 10
    fi
  fi
done

echo ""
echo "⚠️ Timeout: /health did not return 200 OK after $MAX_ATTEMPTS attempts"
echo "Check Railway logs for errors"
echo ""
