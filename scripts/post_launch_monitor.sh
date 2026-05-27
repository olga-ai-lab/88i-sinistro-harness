#!/bin/bash

################################################################################
# Post-Launch Monitoring Script
#
# Purpose: Monitor system health during first 24 hours post-launch
# 
# Usage: ./post_launch_monitor.sh [domain] [duration]
#        ./post_launch_monitor.sh                    # Uses defaults (localhost:8000, 24 hours)
#        ./post_launch_monitor.sh localhost:8000     # Custom domain, 24 hours
#        ./post_launch_monitor.sh localhost:8000 24  # Custom domain, custom duration (hours)
#
# Features:
# - Runs every 5 minutes for 24 hours (or specified duration)
# - Fetches /metrics/performance and /health/detailed endpoints
# - Calculates error rate and checks against thresholds
# - Alerts if error rate > 5% or latency > 150ms
# - Logs all metrics with timestamps
# - Outputs formatted metrics summary
#
# Output Files:
# - post_launch_metrics_YYYYMMDD_HHMMSS.log (main metrics log)
# - post_launch_summary_YYYYMMDD_HHMMSS.txt (formatted summary)
#
################################################################################

set -e

# Configuration
DOMAIN="${1:-localhost:8000}"
DURATION_HOURS="${2:-24}"
PROTOCOL="http"
INTERVAL_MINUTES=5

# Determine protocol based on domain
if [[ "$DOMAIN" == *".app" ]] || [[ "$DOMAIN" == "api."* ]]; then
    PROTOCOL="https"
fi

# Build full URLs
DOMAIN_URL="${PROTOCOL}://${DOMAIN}"
METRICS_URL="${DOMAIN_URL}/metrics/performance"
HEALTH_URL="${DOMAIN_URL}/health/detailed"

# Calculate total iterations (5-minute intervals for N hours)
TOTAL_MINUTES=$((DURATION_HOURS * 60))
TOTAL_ITERATIONS=$((TOTAL_MINUTES / INTERVAL_MINUTES))

# Initialize log files with timestamps
TIMESTAMP_FILE=$(date +%Y%m%d_%H%M%S)
TIMESTAMP_DATE=$(date +%Y%m%d)
LOG_FILE="post_launch_metrics_${TIMESTAMP_FILE}.log"
SUMMARY_FILE="post_launch_summary_${TIMESTAMP_FILE}.txt"
TEMP_DATA_FILE=".post_launch_temp_${TIMESTAMP_FILE}.json"

# Initialize counters and accumulators
ITERATION=0
TOTAL_REQUESTS=0
TOTAL_ERRORS=0
ERROR_RATE_SUM=0
P50_SUM=0
P95_SUM=0
P99_SUM=0
LATENCY_MAX=0
LATENCY_MIN=99999
CPU_MAX=0
MEMORY_MAX=0
ALERT_COUNT=0
DECLARE -A ERROR_TYPES_COUNT
DECLARE -a ALERT_HISTORY

echo "=================================================================================="
echo "Post-Launch Monitoring - Started at $(date +'%Y-%m-%d %H:%M:%S')"
echo "=================================================================================="
echo "Domain:        $DOMAIN_URL"
echo "Metrics URL:   $METRICS_URL"
echo "Health URL:    $HEALTH_URL"
echo "Interval:      ${INTERVAL_MINUTES} minutes"
echo "Duration:      ${DURATION_HOURS} hours (${TOTAL_ITERATIONS} iterations)"
echo "Log File:      $LOG_FILE"
echo "Summary File:  $SUMMARY_FILE"
echo "=================================================================================="
echo ""

# Initialize log files with headers
{
    echo "================================================================================"
    echo "POST-LAUNCH MONITORING LOG"
    echo "================================================================================"
    echo "Start Time: $(date +'%Y-%m-%d %H:%M:%S')"
    echo "Domain: $DOMAIN_URL"
    echo "Monitoring Duration: ${DURATION_HOURS} hours"
    echo "Check Interval: ${INTERVAL_MINUTES} minutes"
    echo "================================================================================"
    echo ""
} | tee "$LOG_FILE" "$SUMMARY_FILE" > /dev/null

# Function to fetch metrics from /metrics/performance endpoint
fetch_performance_metrics() {
    local response=$(curl -s -w "\n%{http_code}" "$METRICS_URL" 2>/dev/null || echo "")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] && [ -n "$body" ]; then
        echo "$body"
    else
        echo "{\"error\": \"HTTP $http_code\"}"
    fi
}

# Function to fetch health from /health/detailed endpoint
fetch_health_status() {
    local response=$(curl -s -w "\n%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] && [ -n "$body" ]; then
        echo "$body"
    else
        echo "{\"error\": \"HTTP $http_code\", \"status\": \"unhealthy\"}"
    fi
}

# Function to extract field safely from JSON
extract_json_field() {
    local json="$1"
    local field="$2"
    local default="${3:-0}"
    
    echo "$json" | jq -r ".$field // $default" 2>/dev/null || echo "$default"
}

# Function to extract nested field from JSON
extract_nested_field() {
    local json="$1"
    local path="$2"
    local default="${3:-0}"
    
    echo "$json" | jq -r "$path // $default" 2>/dev/null || echo "$default"
}

# Function to calculate error rate
calculate_error_rate() {
    local health_json="$1"
    local errors=$(extract_json_field "$health_json" "last_minute_errors" "0")
    local requests=$(extract_json_field "$health_json" "last_minute_requests" "1")
    
    # Avoid division by zero
    if [ "$requests" -eq 0 ]; then
        echo "0"
    else
        # Calculate percentage: (errors / requests) * 100
        awk "BEGIN {printf \"%.2f\", ($errors / $requests) * 100}"
    fi
}

# Function to check for alerts
check_alerts() {
    local error_rate="$1"
    local p95_latency="$2"
    local iteration="$3"
    local current_time="$4"
    
    local alert_triggered=0
    
    # Check error rate threshold (>5%)
    if (( $(echo "$error_rate > 5" | bc -l) )); then
        alert_triggered=1
        local alert_msg="⚠️  ALERT [ERROR RATE] - ${current_time} - Error Rate: ${error_rate}% (threshold: 5%) - Iteration $iteration"
        echo "$alert_msg"
        echo "$alert_msg" >> "$LOG_FILE"
        ALERT_HISTORY+=("$alert_msg")
    fi
    
    # Check latency threshold (>150ms)
    if (( $(echo "$p95_latency > 150" | bc -l) )); then
        alert_triggered=1
        local alert_msg="⚠️  ALERT [LATENCY] - ${current_time} - P95 Latency: ${p95_latency}ms (threshold: 150ms) - Iteration $iteration"
        echo "$alert_msg"
        echo "$alert_msg" >> "$LOG_FILE"
        ALERT_HISTORY+=("$alert_msg")
    fi
    
    return $alert_triggered
}

# Main monitoring loop
while [ $ITERATION -lt $TOTAL_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    CURRENT_TIME=$(date +'%Y-%m-%d %H:%M:%S')
    
    echo ""
    echo "────────────────────────────────────────────────────────────────────────────────"
    echo "Iteration $ITERATION of $TOTAL_ITERATIONS - $CURRENT_TIME"
    echo "────────────────────────────────────────────────────────────────────────────────"
    
    # Fetch metrics
    echo "Fetching metrics from $METRICS_URL..."
    METRICS_RESPONSE=$(fetch_performance_metrics)
    
    echo "Fetching health status from $HEALTH_URL..."
    HEALTH_RESPONSE=$(fetch_health_status)
    
    # Log raw responses
    {
        echo ""
        echo "[$CURRENT_TIME] Iteration $ITERATION"
        echo "─────────────────────────────────────────────────────────────"
        echo "Performance Metrics Response:"
        echo "$METRICS_RESPONSE" | jq . 2>/dev/null || echo "$METRICS_RESPONSE"
        echo ""
        echo "Health Status Response:"
        echo "$HEALTH_RESPONSE" | jq . 2>/dev/null || echo "$HEALTH_RESPONSE"
        echo ""
    } >> "$LOG_FILE"
    
    # Extract metrics (handle both array and object responses)
    if echo "$METRICS_RESPONSE" | jq . &>/dev/null; then
        # Check if it's an array
        if echo "$METRICS_RESPONSE" | jq 'if type == "array" then .[0] else . end' &>/dev/null; then
            METRICS_DATA=$(echo "$METRICS_RESPONSE" | jq 'if type == "array" then .[0] else . end')
        else
            METRICS_DATA="$METRICS_RESPONSE"
        fi
        
        UPTIME=$(extract_json_field "$METRICS_DATA" "uptime_seconds" "0")
        REQUEST_RATE=$(extract_json_field "$METRICS_DATA" "request_rate" "0")
        P50=$(extract_json_field "$METRICS_DATA" "p50_ms" "0")
        P95=$(extract_json_field "$METRICS_DATA" "p95_ms" "0")
        P99=$(extract_json_field "$METRICS_DATA" "p99_ms" "0")
        AVG_LATENCY=$(extract_json_field "$METRICS_DATA" "average_latency_ms" "0")
    else
        UPTIME=0
        REQUEST_RATE=0
        P50=0
        P95=0
        P99=0
        AVG_LATENCY=0
    fi
    
    # Extract health metrics
    if echo "$HEALTH_RESPONSE" | jq . &>/dev/null; then
        HEALTH_STATUS=$(extract_json_field "$HEALTH_RESPONSE" "status" "unknown")
        UPTIME_HEALTH=$(extract_json_field "$HEALTH_RESPONSE" "uptime_seconds" "0")
        DB_STATUS=$(extract_nested_field "$HEALTH_RESPONSE" ".database.status // \"unknown\"" "unknown")
        CPU_USAGE=$(extract_nested_field "$HEALTH_RESPONSE" ".system.cpu_percent // 0" "0")
        MEMORY_USAGE=$(extract_nested_field "$HEALTH_RESPONSE" ".system.memory_percent // 0" "0")
    else
        HEALTH_STATUS="unknown"
        UPTIME_HEALTH=0
        DB_STATUS="unknown"
        CPU_USAGE=0
        MEMORY_USAGE=0
    fi
    
    # Calculate error rate
    ERROR_RATE=$(calculate_error_rate "$HEALTH_RESPONSE")
    LAST_MINUTE_ERRORS=$(extract_json_field "$HEALTH_RESPONSE" "last_minute_errors" "0")
    LAST_MINUTE_REQUESTS=$(extract_json_field "$HEALTH_RESPONSE" "last_minute_requests" "0")
    
    # Accumulate statistics
    TOTAL_REQUESTS=$((TOTAL_REQUESTS + LAST_MINUTE_REQUESTS))
    TOTAL_ERRORS=$((TOTAL_ERRORS + LAST_MINUTE_ERRORS))
    ERROR_RATE_SUM=$(awk "BEGIN {printf \"%.2f\", $ERROR_RATE_SUM + $ERROR_RATE}")
    P50_SUM=$(awk "BEGIN {printf \"%.2f\", $P50_SUM + $P50}")
    P95_SUM=$(awk "BEGIN {printf \"%.2f\", $P95_SUM + $P95}")
    P99_SUM=$(awk "BEGIN {printf \"%.2f\", $P99_SUM + $P99}")
    
    # Track latency extremes
    if (( $(echo "$P95 > $LATENCY_MAX" | bc -l) )); then
        LATENCY_MAX=$P95
    fi
    if (( $(echo "$P95 < $LATENCY_MIN" | bc -l) )); then
        LATENCY_MIN=$P95
    fi
    
    # Track resource usage peaks
    if (( $(echo "$CPU_USAGE > $CPU_MAX" | bc -l) )); then
        CPU_MAX=$CPU_USAGE
    fi
    if (( $(echo "$MEMORY_USAGE > $MEMORY_MAX" | bc -l) )); then
        MEMORY_MAX=$MEMORY_USAGE
    fi
    
    # Display current metrics
    echo ""
    echo "Current Metrics:"
    printf "  Health Status:      %s\n" "$HEALTH_STATUS"
    printf "  Error Rate:         %.2f%% (Last Minute: %d errors / %d requests)\n" "$ERROR_RATE" "$LAST_MINUTE_ERRORS" "$LAST_MINUTE_REQUESTS"
    printf "  Request Rate:       %.2f req/sec\n" "$REQUEST_RATE"
    printf "  P50 Latency:        %.2f ms\n" "$P50"
    printf "  P95 Latency:        %.2f ms\n" "$P95"
    printf "  P99 Latency:        %.2f ms\n" "$P99"
    printf "  CPU Usage:          %.2f%%\n" "$CPU_USAGE"
    printf "  Memory Usage:       %.2f%%\n" "$MEMORY_USAGE"
    printf "  Database:           %s\n" "$DB_STATUS"
    
    # Check for alerts
    check_alerts "$ERROR_RATE" "$P95" "$ITERATION" "$CURRENT_TIME"
    ALERT_COUNT=$((ALERT_COUNT + $?))
    
    # Sleep until next iteration (unless this is the last iteration)
    if [ $ITERATION -lt $TOTAL_ITERATIONS ]; then
        echo ""
        echo "Next check in ${INTERVAL_MINUTES} minutes... (press Ctrl+C to stop)"
        sleep $((INTERVAL_MINUTES * 60))
    fi
done

# Calculate averages
AVG_ERROR_RATE=$(awk "BEGIN {printf \"%.2f\", $ERROR_RATE_SUM / $ITERATION}")
AVG_P50=$(awk "BEGIN {printf \"%.2f\", $P50_SUM / $ITERATION}")
AVG_P95=$(awk "BEGIN {printf \"%.2f\", $P95_SUM / $ITERATION}")
AVG_P99=$(awk "BEGIN {printf \"%.2f\", $P99_SUM / $ITERATION}")

# Calculate availability (assuming 100% if TOTAL_REQUESTS > 0 and no all-down periods)
if [ "$TOTAL_REQUESTS" -eq 0 ]; then
    AVAILABILITY="0%"
else
    AVAILABILITY_PCT=$(awk "BEGIN {printf \"%.2f\", ((($TOTAL_REQUESTS - $TOTAL_ERRORS) / $TOTAL_REQUESTS) * 100)}")
    AVAILABILITY="${AVAILABILITY_PCT}%"
fi

# Generate formatted summary
{
    echo ""
    echo "================================================================================"
    echo "POST-LAUNCH MONITORING - 24-HOUR SUMMARY"
    echo "================================================================================"
    echo "Monitoring Period: $(date +'%Y-%m-%d %H:%M:%S') to $(date +'%Y-%m-%d %H:%M:%S')"
    echo "Domain: $DOMAIN_URL"
    echo "Total Iterations: $ITERATION"
    echo "Check Interval: ${INTERVAL_MINUTES} minutes"
    echo ""
    echo "OVERVIEW"
    echo "────────────────────────────────────────────────────────────────────────────────"
    printf "Total Requests Monitored:    %d\n" "$TOTAL_REQUESTS"
    printf "Total Errors Detected:       %d\n" "$TOTAL_ERRORS"
    printf "Overall Error Rate:          %.2f%%\n" "$AVG_ERROR_RATE"
    printf "Availability (Success Rate): %s\n" "$AVAILABILITY"
    echo ""
    
    echo "PERFORMANCE METRICS"
    echo "────────────────────────────────────────────────────────────────────────────────"
    printf "P50 Latency (Average):       %.2f ms\n" "$AVG_P50"
    printf "P95 Latency (Average):       %.2f ms\n" "$AVG_P95"
    printf "P99 Latency (Average):       %.2f ms\n" "$AVG_P99"
    printf "Max Observed P95 Latency:    %.2f ms\n" "$LATENCY_MAX"
    printf "Min Observed P95 Latency:    %.2f ms\n" "$LATENCY_MIN"
    echo ""
    
    echo "RESOURCE USAGE - PEAK VALUES"
    echo "────────────────────────────────────────────────────────────────────────────────"
    printf "Peak CPU Usage:              %.2f%%\n" "$CPU_MAX"
    printf "Peak Memory Usage:           %.2f%%\n" "$MEMORY_MAX"
    echo ""
    
    echo "ERROR MONITORING"
    echo "────────────────────────────────────────────────────────────────────────────────"
    if [ "$ALERT_COUNT" -eq 0 ]; then
        echo "✅ No alerts triggered during monitoring period"
    else
        echo "⚠️  Total Alerts Triggered: $ALERT_COUNT"
        echo ""
        echo "Alert History:"
        for i in "${!ALERT_HISTORY[@]}"; do
            printf "  %d. %s\n" "$((i + 1))" "${ALERT_HISTORY[$i]}"
        done
    fi
    echo ""
    
    echo "THRESHOLDS & COMPLIANCE"
    echo "────────────────────────────────────────────────────────────────────────────────"
    if (( $(echo "$AVG_ERROR_RATE > 5" | bc -l) )); then
        echo "❌ Error Rate EXCEEDS threshold (>5%)"
    else
        echo "✅ Error Rate within threshold (<5%)"
    fi
    
    if (( $(echo "$AVG_P95 > 150" | bc -l) )); then
        echo "❌ P95 Latency EXCEEDS threshold (>150ms)"
    else
        echo "✅ P95 Latency within threshold (<150ms)"
    fi
    echo ""
    
    echo "================================================================================"
    echo "Monitoring completed at $(date +'%Y-%m-%d %H:%M:%S')"
    echo "================================================================================"
    
} | tee -a "$SUMMARY_FILE"

# Also append raw data to log
{
    echo ""
    echo "================================================================================"
    echo "End of monitoring log"
    echo "================================================================================"
} >> "$LOG_FILE"

echo ""
echo "✅ Post-launch monitoring completed!"
echo ""
echo "Files generated:"
echo "  - Detailed log:  $LOG_FILE"
echo "  - Summary:       $SUMMARY_FILE"
echo ""

# Clean up temp file if it exists
rm -f "$TEMP_DATA_FILE"

exit 0
