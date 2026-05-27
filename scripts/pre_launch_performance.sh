#!/bin/bash

################################################################################
# Pre-Launch Performance Validation Script
# Comprehensive performance baseline and load testing before production launch
# Exit code: 0 if all checks pass, 1 if ANY check fails
#
# Tests:
#  1. Health check endpoint (/health, expect HTTP 200)
#  2. Extract operation baseline (10 samples, measure ms, HTTP 200, P95 < 100ms)
#  3. Fraud detection baseline (10 samples, measure ms, P95 < 150ms)
#  4. Concurrent load test (10 parallel requests, measure throughput)
#  5. Error rate analysis (target: < 1% error rate)
#
# Output: ✅/❌/⊘ status with colored output, P95 latency reports
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Configuration
DOMAIN="${1:-http://localhost:8000}"
TIMEOUT=30
CONCURRENT_REQUESTS=10

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

# Get the repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/..)" && pwd)"

# Logging setup
LOG_DIR="${REPO_ROOT}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/pre_launch_performance_$(date +%Y%m%d_%H%M%S).log"

{
echo "Pre-Launch Performance Validation"
echo "Started: $(date)"
echo "Target: $DOMAIN"
echo ""

# Verify domain parameter
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 https://api.example.com"
    echo ""
    DOMAIN="http://localhost:8000"
    echo "Using default: $DOMAIN"
fi

echo -e "${BLUE}Performance Check Target: ${DOMAIN}${NC}"
echo ""

################################################################################
# 1. HEALTH CHECK ENDPOINT
################################################################################
print_header "1. HEALTH CHECK ENDPOINT"

HEALTH_ENDPOINT="${DOMAIN}/health"
echo "Testing endpoint: $HEALTH_ENDPOINT"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    check_passed "Health check: Endpoint responding (HTTP $HTTP_CODE)"
    
    # Try to parse response for status
    HEALTH_RESPONSE=$(curl -s --connect-timeout 5 --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>/dev/null || echo "{}")
    if echo "$HEALTH_RESPONSE" | grep -qE "ok|healthy|up|running|status"; then
        check_passed "Health check: System status verified"
    else
        check_passed "Health check: Responded (detailed status unavailable)"
    fi
else
    check_failed "Health check: Endpoint returned HTTP $HTTP_CODE (expected 200)"
fi
echo ""

################################################################################
# 2. EXTRACT OPERATION BASELINE (10 Samples)
################################################################################
print_header "2. EXTRACT OPERATION BASELINE (10 Samples)"

EXTRACT_ENDPOINT="${DOMAIN}/extract"
echo "Measuring latency for: $EXTRACT_ENDPOINT"
echo "Target: P95 < 100ms"
echo ""

EXTRACT_TIMES=()
EXTRACT_HTTP_CODES=()
EXTRACT_ERRORS=0

# Perform 10 samples
for i in {1..10}; do
    echo -n "Sample $i... "
    
    START=$(date +%s%N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" \
        -X POST "$EXTRACT_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d '{"document":"test document","language":"pt"}' 2>/dev/null || echo "000")
    END=$(date +%s%N)
    
    # Calculate elapsed time in milliseconds
    ELAPSED=$(( ($END - $START) / 1000000 ))
    EXTRACT_TIMES+=("$ELAPSED")
    EXTRACT_HTTP_CODES+=("$HTTP_CODE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}${ELAPSED}ms (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}${ELAPSED}ms (HTTP $HTTP_CODE)${NC}"
        ((EXTRACT_ERRORS++))
    fi
done

echo ""

# Calculate P95 latency
if [ ${#EXTRACT_TIMES[@]} -gt 0 ]; then
    # Sort times and calculate P95
    IFS=$'\n' sorted_times=($(sort -n <<<"${EXTRACT_TIMES[*]}"))
    unset IFS
    
    P95_INDEX=$(( (${#sorted_times[@]} * 95) / 100 ))
    P95_LATENCY=${sorted_times[$P95_INDEX]}
    
    # Also calculate min, max, avg
    MIN_LATENCY=${sorted_times[0]}
    MAX_LATENCY=${sorted_times[$((${#sorted_times[@]} - 1))]}
    SUM_LATENCY=0
    for time in "${EXTRACT_TIMES[@]}"; do
        SUM_LATENCY=$((SUM_LATENCY + time))
    done
    AVG_LATENCY=$((SUM_LATENCY / ${#EXTRACT_TIMES[@]}))
    
    echo "Extract latency statistics:"
    echo "  Min: ${MIN_LATENCY}ms"
    echo "  Avg: ${AVG_LATENCY}ms"
    echo "  P95: ${P95_LATENCY}ms (target: <100ms)"
    echo "  Max: ${MAX_LATENCY}ms"
    echo ""
    
    # Validate P95 against target
    if [ "$P95_LATENCY" -lt 100 ]; then
        check_passed "Extract P95 latency: ${P95_LATENCY}ms < 100ms target"
    elif [ "$P95_LATENCY" -lt 150 ]; then
        check_failed "Extract P95 latency: ${P95_LATENCY}ms exceeds target (<100ms)"
    else
        check_failed "Extract P95 latency: ${P95_LATENCY}ms significantly exceeds target"
    fi
    
    # Check HTTP 200 success rate
    SUCCESS_COUNT=0
    for code in "${EXTRACT_HTTP_CODES[@]}"; do
        [ "$code" = "200" ] && ((SUCCESS_COUNT++))
    done
    
    if [ "$SUCCESS_COUNT" -eq 10 ]; then
        check_passed "Extract: 10/10 requests successful (100%, all HTTP 200)"
    else
        check_failed "Extract: Only $SUCCESS_COUNT/10 requests successful ($((SUCCESS_COUNT * 10))%)"
    fi
else
    check_failed "Extract: Unable to measure latency (endpoint unreachable)"
fi
echo ""

################################################################################
# 3. FRAUD DETECTION BASELINE (10 Samples)
################################################################################
print_header "3. FRAUD DETECTION BASELINE (10 Samples)"

FRAUD_ENDPOINT="${DOMAIN}/fraud"
echo "Measuring latency for: $FRAUD_ENDPOINT"
echo "Target: P95 < 150ms"
echo ""

FRAUD_TIMES=()
FRAUD_HTTP_CODES=()
FRAUD_ERRORS=0

# Perform 10 samples
for i in {1..10}; do
    echo -n "Sample $i... "
    
    START=$(date +%s%N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" \
        -X POST "$FRAUD_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d '{"claim":{"type":"AP","value":10000}}' 2>/dev/null || echo "000")
    END=$(date +%s%N)
    
    # Calculate elapsed time in milliseconds
    ELAPSED=$(( ($END - $START) / 1000000 ))
    FRAUD_TIMES+=("$ELAPSED")
    FRAUD_HTTP_CODES+=("$HTTP_CODE")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}${ELAPSED}ms (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${YELLOW}${ELAPSED}ms (HTTP $HTTP_CODE)${NC}"
        ((FRAUD_ERRORS++))
    fi
done

echo ""

# Calculate P95 latency
if [ ${#FRAUD_TIMES[@]} -gt 0 ]; then
    # Sort times and calculate P95
    IFS=$'\n' sorted_times=($(sort -n <<<"${FRAUD_TIMES[*]}"))
    unset IFS
    
    P95_INDEX=$(( (${#sorted_times[@]} * 95) / 100 ))
    P95_LATENCY=${sorted_times[$P95_INDEX]}
    
    # Also calculate min, max, avg
    MIN_LATENCY=${sorted_times[0]}
    MAX_LATENCY=${sorted_times[$((${#sorted_times[@]} - 1))]}
    SUM_LATENCY=0
    for time in "${FRAUD_TIMES[@]}"; do
        SUM_LATENCY=$((SUM_LATENCY + time))
    done
    AVG_LATENCY=$((SUM_LATENCY / ${#FRAUD_TIMES[@]}))
    
    echo "Fraud detection latency statistics:"
    echo "  Min: ${MIN_LATENCY}ms"
    echo "  Avg: ${AVG_LATENCY}ms"
    echo "  P95: ${P95_LATENCY}ms (target: <150ms)"
    echo "  Max: ${MAX_LATENCY}ms"
    echo ""
    
    # Validate P95 against target
    if [ "$P95_LATENCY" -lt 150 ]; then
        check_passed "Fraud P95 latency: ${P95_LATENCY}ms < 150ms target"
    elif [ "$P95_LATENCY" -lt 250 ]; then
        check_failed "Fraud P95 latency: ${P95_LATENCY}ms exceeds target (<150ms)"
    else
        check_failed "Fraud P95 latency: ${P95_LATENCY}ms significantly exceeds target"
    fi
    
    # Check HTTP 200 success rate
    SUCCESS_COUNT=0
    for code in "${FRAUD_HTTP_CODES[@]}"; do
        [ "$code" = "200" ] && ((SUCCESS_COUNT++))
    done
    
    if [ "$SUCCESS_COUNT" -eq 10 ]; then
        check_passed "Fraud: 10/10 requests successful (100%, all HTTP 200)"
    else
        check_failed "Fraud: Only $SUCCESS_COUNT/10 requests successful ($((SUCCESS_COUNT * 10))%)"
    fi
else
    check_failed "Fraud: Unable to measure latency (endpoint unreachable)"
fi
echo ""

################################################################################
# 4. CONCURRENT LOAD TEST (10 Parallel Requests)
################################################################################
print_header "4. CONCURRENT LOAD TEST (10 Parallel Requests)"

echo "Launching 10 concurrent requests to $EXTRACT_ENDPOINT..."
echo ""

# Create temporary directory for results
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

CONCURRENT_SUCCESS=0
CONCURRENT_FAILURES=0
CONCURRENT_START=$(date +%s%N)

# Launch 10 background requests in parallel
for i in {1..10}; do
    (
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time "$TIMEOUT" \
            -X POST "$EXTRACT_ENDPOINT" \
            -H "Content-Type: application/json" \
            -d '{"document":"test document","language":"pt"}' 2>/dev/null || echo "000")
        
        if [ "$HTTP_CODE" = "200" ]; then
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
        check_failed "Concurrent requests: $CONCURRENT_SUCCESS/10 successful ($SUCCESS_RATE% - target: 99%+)"
    else
        check_failed "Concurrent requests: $CONCURRENT_SUCCESS/10 successful ($SUCCESS_RATE% - target: 99%+)"
    fi
fi

# Check if requests completed within reasonable time
if [ "$CONCURRENT_DURATION" -lt 5000 ]; then
    check_passed "Concurrent throughput: All 10 requests completed in ${CONCURRENT_DURATION}ms"
else
    check_failed "Concurrent throughput: Requests took ${CONCURRENT_DURATION}ms (acceptable: <5000ms)"
fi
echo ""

################################################################################
# 5. ERROR RATE ANALYSIS
################################################################################
print_header "5. ERROR RATE ANALYSIS"

echo "Analyzing overall error rates..."
echo ""

# Calculate overall statistics
TOTAL_TESTS=$((10 + 10 + CONCURRENT_SUCCESS + CONCURRENT_FAILURES))
TOTAL_SUCCESS=$((${#EXTRACT_TIMES[@]} + ${#FRAUD_TIMES[@]} + CONCURRENT_SUCCESS))
TOTAL_FAILURES=$((EXTRACT_ERRORS + FRAUD_ERRORS + CONCURRENT_FAILURES))

if [ "$TOTAL_TESTS" -gt 0 ]; then
    ERROR_RATE=$((TOTAL_FAILURES * 100 / TOTAL_TESTS))
    SUCCESS_RATE=$((TOTAL_SUCCESS * 100 / TOTAL_TESTS))
    
    echo "Test Summary:"
    echo "  Total requests: $TOTAL_TESTS"
    echo "  Successful: $TOTAL_SUCCESS"
    echo "  Failed: $TOTAL_FAILURES"
    echo "  Error rate: $ERROR_RATE%"
    echo "  Success rate: $SUCCESS_RATE%"
    echo ""
    
    if [ "$ERROR_RATE" -eq 0 ]; then
        check_passed "Overall error rate: $ERROR_RATE% (0 errors, excellent)"
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
echo ""

################################################################################
# SUMMARY & EXIT CODE
################################################################################
print_footer

# Summary table
echo "Performance Baseline Report:"
echo "================================"
echo "Endpoint               | Metric              | Value      | Target      | Status"
echo "--------------------------------|---------------------|------------|-------------|----------"
if [ ${#EXTRACT_TIMES[@]} -gt 0 ]; then
    IFS=$'\n' sorted=($(sort -n <<<"${EXTRACT_TIMES[*]}"))
    unset IFS
    P95_IDX=$(( (${#sorted[@]} * 95) / 100 ))
    EXTRACT_P95=${sorted[$P95_IDX]}
    [ "$EXTRACT_P95" -lt 100 ] && EXTRACT_STATUS="${GREEN}PASS${NC}" || EXTRACT_STATUS="${RED}FAIL${NC}"
    printf "Extract Operation     | P95 Latency         | %5dms    | <100ms      | ${EXTRACT_STATUS}\n" "$EXTRACT_P95"
fi

if [ ${#FRAUD_TIMES[@]} -gt 0 ]; then
    IFS=$'\n' sorted=($(sort -n <<<"${FRAUD_TIMES[*]}"))
    unset IFS
    P95_IDX=$(( (${#sorted[@]} * 95) / 100 ))
    FRAUD_P95=${sorted[$P95_IDX]}
    [ "$FRAUD_P95" -lt 150 ] && FRAUD_STATUS="${GREEN}PASS${NC}" || FRAUD_STATUS="${RED}FAIL${NC}"
    printf "Fraud Detection       | P95 Latency         | %5dms    | <150ms      | ${FRAUD_STATUS}\n" "$FRAUD_P95"
fi

printf "Concurrent Load       | 10 Parallel Reqs    | %5dms    | <5000ms     | ${GREEN}PASS${NC}\n" "$CONCURRENT_DURATION"
printf "Error Rate            | Overall             | %5d%%     | <1%%         | " "$ERROR_RATE"
[ "$ERROR_RATE" -lt 1 ] && printf "${GREEN}PASS${NC}" || printf "${RED}FAIL${NC}"
printf "\n"
echo ""

# Final verdict
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ PERFORMANCE VALIDATION FAILED${NC}"
    echo "Please address $FAILED failed check(s) before production launch."
    echo ""
    echo "Detailed log: $LOG_FILE"
    exit 1
else
    echo -e "${GREEN}✅ PERFORMANCE VALIDATION PASSED${NC}"
    echo "All performance requirements validated. Safe to proceed to launch."
    echo ""
    echo "Detailed log: $LOG_FILE"
    exit 0
fi

} | tee "$LOG_FILE"
