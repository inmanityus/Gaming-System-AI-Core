#!/bin/bash
set -euo pipefail

SERVICE_NAME=$1
IMAGE_TAG=$2
REGION=${AWS_REGION:-us-east-1}
MONITORING_DURATION=600  # 10 minutes
CHECK_INTERVAL=30       # Check every 30 seconds

echo "Monitoring production deployment for $SERVICE_NAME with tag $IMAGE_TAG"

# Function to check CloudWatch alarms
check_alarms() {
    local alarm_prefix="${SERVICE_NAME}-production"
    
    # Check various alarm types
    local alarm_names=(
        "${alarm_prefix}-error-rate"
        "${alarm_prefix}-latency"
        "${alarm_prefix}-cpu-usage"
        "${alarm_prefix}-memory-usage"
        "${alarm_prefix}-http-5xx"
        "${alarm_prefix}-http-4xx"
    )
    
    local alarms_in_alarm_state=0
    
    for alarm_name in "${alarm_names[@]}"; do
        alarm_state=$(aws cloudwatch describe-alarms \
            --alarm-names "$alarm_name" \
            --region "$REGION" \
            --query 'MetricAlarms[0].StateValue' \
            --output text 2>/dev/null || echo "NOT_FOUND")
            
        if [ "$alarm_state" == "ALARM" ]; then
            echo "❌ ALARM: $alarm_name is in ALARM state"
            ((alarms_in_alarm_state++))
        elif [ "$alarm_state" == "INSUFFICIENT_DATA" ]; then
            echo "⚠️  WARNING: $alarm_name has insufficient data"
        elif [ "$alarm_state" == "OK" ]; then
            echo "✅ OK: $alarm_name"
        fi
    done
    
    return $alarms_in_alarm_state
}

# Function to check service health
check_service_health() {
    local cluster="gaming-system-cluster"
    
    # Get service details
    local service_info=$(aws ecs describe-services \
        --cluster "$cluster" \
        --services "$SERVICE_NAME" \
        --region "$REGION" \
        --query 'services[0]')
        
    local desired_count=$(echo "$service_info" | jq -r '.desiredCount')
    local running_count=$(echo "$service_info" | jq -r '.runningCount')
    local pending_count=$(echo "$service_info" | jq -r '.pendingCount')
    
    echo "Service status: Desired=$desired_count, Running=$running_count, Pending=$pending_count"
    
    if [ "$running_count" -lt "$desired_count" ]; then
        echo "❌ ERROR: Not all tasks are running"
        return 1
    fi
    
    if [ "$pending_count" -gt 0 ]; then
        echo "⚠️  WARNING: Tasks still pending"
    fi
    
    # Check recent events for errors
    local recent_events=$(aws ecs describe-services \
        --cluster "$cluster" \
        --services "$SERVICE_NAME" \
        --region "$REGION" \
        --query 'services[0].events[:5]')
        
    if echo "$recent_events" | jq -r '.[].message' | grep -i "error\|failed" > /dev/null; then
        echo "❌ ERROR: Recent service events contain errors"
        echo "$recent_events" | jq -r '.[] | "\(.createdAt): \(.message)"'
        return 1
    fi
    
    return 0
}

# Function to check application metrics
check_app_metrics() {
    local namespace="Gaming/System/Services"
    local metric_name="RequestCount"
    
    # Get request count for last 5 minutes
    local end_time=$(date -u +%Y-%m-%dT%H:%M:%S)
    local start_time=$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S)
    
    local request_count=$(aws cloudwatch get-metric-statistics \
        --namespace "$namespace" \
        --metric-name "$metric_name" \
        --dimensions Name=ServiceName,Value="$SERVICE_NAME" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Sum \
        --region "$REGION" \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")
        
    if [ "$request_count" == "0" ] || [ "$request_count" == "None" ]; then
        echo "⚠️  WARNING: No requests received in last 5 minutes"
        return 1
    else
        echo "✅ Application receiving traffic: $request_count requests in last 5 minutes"
    fi
    
    # Check error rate
    local error_count=$(aws cloudwatch get-metric-statistics \
        --namespace "$namespace" \
        --metric-name "ErrorCount" \
        --dimensions Name=ServiceName,Value="$SERVICE_NAME" \
        --start-time "$start_time" \
        --end-time "$end_time" \
        --period 300 \
        --statistics Sum \
        --region "$REGION" \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null || echo "0")
        
    if [ "$error_count" != "0" ] && [ "$error_count" != "None" ]; then
        local error_rate=$(echo "scale=2; $error_count / $request_count * 100" | bc)
        echo "⚠️  Error rate: ${error_rate}%"
        
        # Fail if error rate > 5%
        if (( $(echo "$error_rate > 5" | bc -l) )); then
            echo "❌ ERROR: Error rate exceeds 5% threshold"
            return 1
        fi
    fi
    
    return 0
}

# Function to perform synthetic health check
perform_health_check() {
    local service_url="https://api.bodybrokergame.com/${SERVICE_NAME}/health"
    
    # Perform health check
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$service_url" --max-time 5 || echo "000")
    
    if [ "$response_code" == "200" ]; then
        echo "✅ Health check passed (HTTP $response_code)"
        return 0
    else
        echo "❌ Health check failed (HTTP $response_code)"
        return 1
    fi
}

# Main monitoring loop
echo "Starting production deployment monitoring..."
echo "Duration: ${MONITORING_DURATION}s, Check interval: ${CHECK_INTERVAL}s"
echo "================================================"

start_time=$(date +%s)
alarm_threshold=3
consecutive_failures=0
max_consecutive_failures=2

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $MONITORING_DURATION ]; then
        echo "Monitoring period completed successfully"
        break
    fi
    
    echo ""
    echo "Check at $(date) (${elapsed}s elapsed)"
    echo "----------------------------------------"
    
    failures=0
    
    # Check CloudWatch alarms
    if ! check_alarms; then
        ((failures++))
    fi
    
    # Check service health
    if ! check_service_health; then
        ((failures++))
    fi
    
    # Check application metrics
    if ! check_app_metrics; then
        ((failures++))
    fi
    
    # Perform health check
    if ! perform_health_check; then
        ((failures++))
    fi
    
    # Evaluate results
    if [ $failures -eq 0 ]; then
        echo "✅ All checks passed"
        consecutive_failures=0
    else
        echo "❌ $failures checks failed"
        ((consecutive_failures++))
        
        if [ $consecutive_failures -ge $max_consecutive_failures ]; then
            echo "CRITICAL: $consecutive_failures consecutive check failures"
            echo "Triggering automatic rollback..."
            exit 1
        fi
    fi
    
    # Wait before next check
    sleep $CHECK_INTERVAL
done

echo ""
echo "================================================"
echo "✅ Production deployment monitoring completed successfully"
echo "Service $SERVICE_NAME with tag $IMAGE_TAG is stable"
