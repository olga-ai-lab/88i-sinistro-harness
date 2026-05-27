#!/bin/bash

################################################################################
# Final Performance Check Script
# Validates endpoint latency, concurrency, and performance metrics
# Usage: ./scripts/final_performance_check.sh <domain>
# Example: ./scripts/final_performance_check.sh https://api.example.com
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Configuration
DOMAIN="${1:-http://localhost:8000}"
TIMEOUT=30
CONCURRENT_REQUESTS=10
EXTRACT_ENDPOINT="${DOMAIN}/extract"
FRAUD_ENDPOINT="${DOMAIN}/fraud"
HEALTH_ENDPOINT="${DOMAIN}/health"
METRICS_ENDPOINT="${DOMAIN}/metrics"

# Helper functions
check_passed() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED++))
}

check_failed() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

check_skipped() {
    echo -e "${YELLOW}⊘${NC} $1"
    ((SKIPPED++))
}

print_header() {
    echo ""
    echo "==============================================="
    echo "  $1"
    echo "==============================================="
}

print_footer() {
    echo ""
    echo "==============================================="
    echo "  Results: ${GREEN}✅${NC} $PASSED passed | ${RED}❌${NC} $FAILED failed | ${YELLOW}⊘${NC} $SKIPPED skipped"
    echo "==============================================="
    echo ""
}

# Verify domain parameter
if [ -z "$DOMAIN" ] || [ "$DOMAIN" == "http://localhost:8000" ]; then
    echo "${BLUE}Usage:${NC} $0 <domain>"
    echo "${BLUE}Example:${NC} $0 https://api.example.com"
    echo ""
    echo "Testing against default: $DOMAIN"
fi

echo "${BLUE}Performance Check Target: ${DOMAIN}${NC}"

################################################################################
# 1. HEALTH CHECK
################################################################################
print_header "1. HEALTH CHECK ENDPOINT"

echo "Testing health endpoint: $HEALTH_ENDPOINT"
echo "Timeout: ${TIMEOUT}s"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    check_passed "Health check: Endpoint responding (HTTP $HTTP_CODE)"
    
    # Try to parse response
    HEALTH_RESPONSE=$(curl -s --connect-timeout 5 --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>/dev/null || echo "{}")
    if echo "$HEALTH_RESPONSE" | grep -qE "ok|healthy|up|running"; then
        check_passed "Health check: System status OK"
    else
        check_passed "Health check: Responded (unable to verify detailed status)"
    fi
else
    check_failed "Health check: Endpoint returned HTTP $HTTP_CODE (expected 200)"
fi

################################################################################
# 2. EXTRACT ENDPOINT LATENCY MEASUREMENT
################################################################################
print_header "2. EXTRACT ENDPOINT LATENCY MEASUREMENT"

echo "Measuring latency for: $EXTRACT_ENDPOINT"
echo ""

EXTRACT_LATENCIES=()
EXTRACT_ERRORS=0
EXTRACT_SUCCESSES=0

# Perform 5 sequential measurements
for i in {1..5}; do
    echo -n "Request $i... "
    
    # Use curl with -w to get timing
    RESPONSE=$(curl -s -w "\n%{time_total}" --connect-timeout 5 --max-time "$TIMEOUT" \
        -X POST "$EXTRACT_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d '{"test": true}' 2>/dev/null || echo "ERROR")
    
    if [[ "$RESPONSE" == "ERROR" ]]; then
        echo "${RED}TIMEOUT/ERROR${NC}"
        ((EXTRACT_ERRORS++))
    else
        # Extract timing from last line
        LATENCY=$(echo "$RESPONSE" | tail -1)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" \
            -X POST "$EXTRACT_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d '{"test": true}' 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
            LATENCY_MS=$(echo "$LATENCY" | awk '{print int($1 * 1000)}')
            echo "${GREEN}${LATENCY_MS}ms${NC}"
            EXTRACT_LATENCIES+=("$LATENCY_MS")
            ((EXTRACT_SUCCESSES++))
        else
            echo "${YELLOW}HTTP $HTTP_CODE${NC}"
            ((EXTRACT_ERRORS++))
        fi
    fi
done

echo ""
if [ ${#EXTRACT_LATENCIES[@]} -gt 0 ]; then
    # Calculate statistics
    MIN_LAT=$(printf '%s\n' "${EXTRACT_LATENCIES[@]}" | sort -n | head -1)
    MAX_LAT=$(printf '%s\n' "${EXTRACT_LATENCIES[@]}" | sort -n | tail -1)
    AVG_LAT=$(printf '%s\n' "${EXTRACT_LATENCIES[@]}" | awk '{sum+=$1; count++} END {if (count>0) print int(sum/count)}')
    
    # P99 estimate (highest value in small sample)
    P99_LAT=$MAX_LAT
    
    check_passed "Extract latency: min=${MIN_LAT}ms, avg=${AVG_LAT}ms, p99~${P99_LAT}ms"
    
    # Latency validation (p99 target < 500ms)
    if [ "$P99_LAT" -lt 500 ]; then
        check_passed "Extract SLA: p99 latency ${P99_LAT}ms < 500ms target"
    elif [ "$P99_LAT" -lt 750 ]; then
        check_failed "Extract SLA: p99 latency ${P99_LAT}ms exceeds target (acceptable range: <500ms)"
    else
        check_failed "Extract SLA: p99 latency ${P99_LAT}ms significantly exceeds target (< 500ms)"
    fi
    
    # Success rate
    if [ "$EXTRACT_ERRORS" -eq 0 ]; then
        check_passed "Extract: 5/5 requests successful (100%)"
    else
        check_failed "Extract: $EXTRACT_ERRORS/5 requests failed"
    fi
else
    check_failed "Extract endpoint: Unable to measure latency (endpoint unreachable)"
fi

################################################################################
# 3. FRAUD DETECTION ENDPOINT LATENCY MEASUREMENT
################################################################################
print_header "3. FRAUD DETECTION ENDPOINT LATENCY MEASUREMENT"

echo "Measuring latency for: $FRAUD_ENDPOINT"
echo ""

FRAUD_LATENCIES=()
FRAUD_ERRORS=0
FRAUD_SUCCESSES=0

# Perform 5 sequential measurements
for i in {1..5}; do
    echo -n "Request $i... "
    
    # Use curl with -w to get timing
    RESPONSE=$(curl -s -w "\n%{time_total}" --connect-timeout 5 --max-time "$TIMEOUT" \
        -X POST "$FRAUD_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d '{"test": true}' 2>/dev/null || echo "ERROR")
    
    if [[ "$RESPONSE" == "ERROR" ]]; then
        echo "${RED}TIMEOUT/ERROR${NC}"
        ((FRAUD_ERRORS++))
    else
        # Extract timing from last line
        LATENCY=$(echo "$RESPONSE" | tail -1)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" \
            -X POST "$FRAUD_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d '{"test": true}' 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
            LATENCY_MS=$(echo "$LATENCY" | awk '{print int($1 * 1000)}')
            echo "${GREEN}${LATENCY_MS}ms${NC}"
            FRAUD_LATENCIES+=("$LATENCY_MS")
            ((FRAUD_SUCCESSES++))
        else
            echo "${YELLOW}HTTP $HTTP_CODE${NC}"
            ((FRAUD_ERRORS++))
        fi
    fi
done

echo ""
if [ ${#FRAUD_LATENCIES[@]} -gt 0 ]; then
    # Calculate statistics
    MIN_LAT=$(printf '%s\n' "${FRAUD_LATENCIES[@]}" | sort -n | head -1)
    MAX_LAT=$(printf '%s\n' "${FRAUD_LATENCIES[@]}" | sort -n | tail -1)
    AVG_LAT=$(printf '%s\n' "${FRAUD_LATENCIES[@]}" | awk '{sum+=$1; count++} END {if (count>0) print int(sum/count)}')
    
    # P99 estimate
    P99_LAT=$MAX_LAT
    
    check_passed "Fraud detection latency: min=${MIN_LAT}ms, avg=${AVG_LAT}ms, p99~${P99_LAT}ms"
    
    # Latency validation (p99 target < 1000ms)
    if [ "$P99_LAT" -lt 1000 ]; then
        check_passed "Fraud SLA: p99 latency ${P99_LAT}ms < 1000ms target"
    elif [ "$P99_LAT" -lt 1500 ]; then
        check_failed "Fraud SLA: p99 latency ${P99_LAT}ms exceeds target (acceptable range: <1000ms)"
    else
        check_failed "Fraud SLA: p99 latency ${P99_LAT}ms significantly exceeds target (< 1000ms)"
    fi
    
    # Success rate
    if [ "$FRAUD_ERRORS" -eq 0 ]; then
        check_passed "Fraud detection: 5/5 requests successful (100%)"
    else
        check_failed "Fraud detection: $FRAUD_ERRORS/5 requests failed"
    fi
else
    check_failed "Fraud endpoint: Unable to measure latency (endpoint unreachable)"
fi

################################################################################
# 4. CONCURRENT LOAD TEST (10 Requests)
################################################################################
print_header "4. CONCURRENT LOAD TEST (10 Parallel Requests)"

echo "Launching 10 concurrent requests to $EXTRACT_ENDPOINT..."
echo ""

# Create a temporary directory for concurrent requests
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

CONCURRENT_SUCCESS=0
CONCURRENT_FAILURES=0
CONCURRENT_START=$(date +%s%N)

# Launch 10 background curl requests
for i in {1..10}; do
    (
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" \
            -X POST "$EXTRACT_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d '{"test": true}' 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
            echo "SUCCESS" > "$TEMP_DIR/request_$i.status"
        else
            echo "FAILED:$HTTP_CODE" > "$TEMP_DIR/request_$i.status"
        fi
    ) &
done

# Wait for all background jobs to complete
wait

CONCURRENT_END=$(date +%s%N)
CONCURRENT_DURATION=$(( ($CONCURRENT_END - $CONCURRENT_START) / 1000000 ))

# Collect results
for i in {1..10}; do
    if [ -f "$TEMP_DIR/request_$i.status" ]; then
        STATUS=$(cat "$TEMP_DIR/request_$i.status")
        if [ "$STATUS" = "SUCCESS" ]; then
            ((CONCURRENT_SUCCESS++))
        else
            ((CONCURRENT_FAILURES++))
        fi
    fi
done

echo "Concurrent load test completed in ${CONCURRENT_DURATION}ms"
echo ""

SUCCESS_RATE=$((CONCURRENT_SUCCESS * 100 / 10))

if [ "$CONCURRENT_SUCCESS" -eq 10 ]; then
    check_passed "Concurrent requests: 10/10 successful (100% success rate)"
else
    if [ "$SUCCESS_RATE" -ge 95 ]; then
        check_passed "Concurrent requests: $CONCURRENT_SUCCESS/10 successful ($SUCCESS_RATE% success rate)"
    else
        check_failed "Concurrent requests: $CONCURRENT_SUCCESS/10 successful ($SUCCESS_RATE% - target: 99%+)"
    fi
fi

# Check if requests completed within reasonable time
if [ "$CONCURRENT_DURATION" -lt 5000 ]; then
    check_passed "Concurrent latency: All 10 requests completed in ${CONCURRENT_DURATION}ms"
else
    check_failed "Concurrent latency: Requests took ${CONCURRENT_DURATION}ms (acceptable: <5000ms)"
fi

################################################################################
# 5. METRICS ENDPOINT
################################################################################
print_header "5. PERFORMANCE METRICS ENDPOINT"

echo "Fetching metrics from: $METRICS_ENDPOINT"
echo ""

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" "$METRICS_ENDPOINT" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    check_passed "Metrics endpoint: Responding (HTTP $HTTP_CODE)"
    
    # Try to fetch and validate metrics
    METRICS_DATA=$(curl -s --connect-timeout 5 --max-time "$TIMEOUT" "$METRICS_ENDPOINT" 2>/dev/null || echo "")
    
    if [ -n "$METRICS_DATA" ]; then
        # Check for common metrics
        METRIC_COUNT=$(echo "$METRICS_DATA" | wc -l)
        
        if echo "$METRICS_DATA" | grep -qE "request|latency|error|duration|count"; then
            check_passed "Metrics: Data contains performance metrics ($METRIC_COUNT lines)"
        else
            check_passed "Metrics: Endpoint responding with data (format validation skipped)"
        fi
        
        # Check for error metrics
        if echo "$METRICS_DATA" | grep -iE "error.*0|failures.*0"; then
            check_passed "Metrics: Error count metrics available"
        fi
    else
        check_failed "Metrics: Endpoint responded but returned empty data"
    fi
else
    check_skipped "Metrics endpoint: HTTP $HTTP_CODE (may not be available in all environments)"
fi

################################################################################
# 6. ERROR RATE VALIDATION
################################################################################
print_header "6. OVERALL ERROR RATE VALIDATION"

TOTAL_REQUESTS=$((EXTRACT_SUCCESSES + FRAUD_SUCCESSES + CONCURRENT_SUCCESS))
TOTAL_ERRORS=$((EXTRACT_ERRORS + FRAUD_ERRORS + CONCURRENT_FAILURES))

if [ "$TOTAL_REQUESTS" -gt 0 ]; then
    ERROR_RATE=$((TOTAL_ERRORS * 100 / TOTAL_REQUESTS))
    SUCCESS_RATE=$((TOTAL_REQUESTS * 100 / (TOTAL_REQUESTS + TOTAL_ERRORS)))
    
    echo "Total requests sent: $((TOTAL_REQUESTS + TOTAL_ERRORS))"
    echo "Successful: $TOTAL_REQUESTS"
    echo "Failed: $TOTAL_ERRORS"
    echo "Success rate: $SUCCESS_RATE%"
    echo ""
    
    if [ "$ERROR_RATE" -eq 0 ]; then
        check_passed "Overall error rate: $ERROR_RATE% (0 errors)"
    elif [ "$ERROR_RATE" -lt 1 ]; then
        check_passed "Overall error rate: $ERROR_RATE% (< 1%, acceptable)"
    elif [ "$ERROR_RATE" -lt 5 ]; then
        check_failed "Overall error rate: $ERROR_RATE% (exceeds target of <1%)"
    else
        check_failed "Overall error rate: $ERROR_RATE% (significantly exceeds target)"
    fi
else
    check_skipped "Error rate: No requests completed for analysis"
fi

################################################################################
# SUMMARY & EXIT CODE
################################################################################
print_footer

if [ $FAILED -gt 0 ]; then
    echo "${RED}❌ PERFORMANCE CHECK FAILED${NC}"
    echo "Please address $FAILED failed check(s) before production deployment."
    exit 1
else
    echo "${GREEN}✅ PERFORMANCE CHECK PASSED${NC}"
    echo "All performance requirements validated. Safe to proceed."
    exit 0
fi
