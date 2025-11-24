#!/bin/bash
# Local debugging script for Lambda functions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "EC2 Auto-Recovery System - Local Debug"
echo "=========================================="

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }

echo ""
echo "Installing dependencies..."
cd "$PROJECT_ROOT"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "No requirements.txt found. Installing basic dependencies..."
    pip3 install boto3 pydantic
fi

echo ""
echo "Setting up test environment variables..."
export AWS_REGION="${AWS_REGION:-us-east-1}"
export RECOVERY_EVENTS_TABLE="ec2-auto-recovery-recovery-events"
export PREDICTION_EVENTS_TABLE="ec2-auto-recovery-prediction-events"
export INSTANCE_CONFIG_TABLE="ec2-auto-recovery-instance-config"
export NOTIFICATION_ENABLED="true"

echo ""
echo "Available test functions:"
echo "1. Test predictive monitor"
echo "2. Test health monitor"
echo "3. Test auto recovery"
echo "4. Test notifier"
echo ""

read -p "Select function to test (1-4): " -r choice

case $choice in
    1)
        echo "Testing predictive monitor..."
        cd "$PROJECT_ROOT/src/lambda"
        python3 -c "
import sys
import json
from monitor.predictive_monitor import lambda_handler

event = {
    'source': 'manual-test',
    'detail': {}
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
        ;;
    2)
        echo "Testing health monitor..."
        read -p "Enter instance ID to test: " -r instance_id
        cd "$PROJECT_ROOT/src/lambda"
        python3 -c "
import sys
import json
from monitor.health_monitor import lambda_handler

event = {
    'source': 'aws.ec2',
    'detail': {
        'instance-id': '$instance_id'
    }
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
        ;;
    3)
        echo "Testing auto recovery..."
        read -p "Enter instance ID to test: " -r instance_id
        cd "$PROJECT_ROOT/src/lambda"
        python3 -c "
import sys
import json
from auto_recovery.recovery_engine import lambda_handler

event = {
    'instance_id': '$instance_id',
    'trigger_type': 'health_check'
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
        ;;
    4)
        echo "Testing notifier..."
        read -p "Enter instance ID to test: " -r instance_id
        cd "$PROJECT_ROOT/src/lambda"
        python3 -c "
import sys
import json
from notifier.notification_handler import lambda_handler

event = {
    'instance_id': '$instance_id',
    'trigger_cause': 'test',
    'action_taken': 'safe_restart',
    'result': {
        'success': True,
        'timestamp': '2024-01-01T00:00:00Z'
    }
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Test completed!"

