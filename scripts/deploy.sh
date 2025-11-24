#!/bin/bash
# Deployment script for EC2 Auto-Recovery System

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/infra/terraform"

echo "=========================================="
echo "EC2 Auto-Recovery System - Deployment"
echo "=========================================="

# Check prerequisites
command -v terraform >/dev/null 2>&1 || { echo "Terraform is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed. Aborting." >&2; exit 1; }

# Check if AWS credentials are configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "Error: AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo ""
echo "Step 1: Installing Python dependencies..."
cd "$PROJECT_ROOT"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --target src/lambda/
else
    echo "No requirements.txt found. Assuming boto3 is available in Lambda runtime."
fi

echo ""
echo "Step 2: Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init

echo ""
echo "Step 3: Validating Terraform configuration..."
terraform validate

echo ""
echo "Step 4: Planning Terraform deployment..."
terraform plan -out=tfplan

echo ""
read -p "Do you want to apply these changes? (yes/no): " -r
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo ""
    echo "Step 5: Applying Terraform configuration..."
    terraform apply tfplan
    rm -f tfplan
    
    echo ""
    echo "=========================================="
    echo "Deployment completed successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Tag your EC2 instances with 'AutoRecovery=enabled' to enable monitoring"
    echo "2. Configure SNS topic subscriptions if needed"
    echo "3. Set up Slack/Teams webhooks in Terraform variables if desired"
    echo ""
    terraform output
else
    echo "Deployment cancelled."
    rm -f tfplan
    exit 0
fi

