#!/bin/bash
# Test Slack Notification Script
# This script invokes the notifier Lambda function to send a test notification to Slack

INSTANCE_ID="${1:-i-test1234567890}"
REGION="${2:-us-east-1}"

echo "=========================================="
echo "Testing Slack Notification"
echo "=========================================="
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
if [ -z "$ACCOUNT_ID" ]; then
    echo "Error: AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "AWS Account: $ACCOUNT_ID"
echo "Region: $REGION"
echo "Instance ID: $INSTANCE_ID"
echo ""

# Create test payload
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PAYLOAD=$(cat <<EOF
{
  "instance_id": "$INSTANCE_ID",
  "trigger_cause": "test",
  "action_taken": "test_notification",
  "result": {
    "success": true,
    "timestamp": "$TIMESTAMP",
    "message": "This is a test notification from EC2 Auto-Recovery System"
  }
}
EOF
)

echo "Payload:"
echo "$PAYLOAD" | jq .
echo ""

# Invoke Lambda function
echo "Invoking notifier Lambda function..."

aws lambda invoke \
    --function-name "ec2-auto-recovery-notifier" \
    --payload "$PAYLOAD" \
    --region "$REGION" \
    --cli-binary-format raw-in-base64-out \
    response.json

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Notification sent successfully!"
    echo "=========================================="
    echo ""
    echo "Check your Slack channel: #team-collab"
    echo ""
    
    # Show response
    if [ -f "response.json" ]; then
        echo "Lambda Response:"
        cat response.json | jq .
        rm -f response.json
    fi
else
    echo ""
    echo "Error: Failed to invoke Lambda function"
    exit 1
fi

