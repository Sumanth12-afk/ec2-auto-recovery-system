#!/bin/bash
# Teardown script for EC2 Auto-Recovery System

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/infra/terraform"

echo "=========================================="
echo "EC2 Auto-Recovery System - Teardown"
echo "=========================================="

# Check prerequisites
command -v terraform >/dev/null 2>&1 || { echo "Terraform is required but not installed. Aborting." >&2; exit 1; }

# Check if AWS credentials are configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "Error: AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo ""
echo "WARNING: This will destroy all resources created by Terraform!"
echo "This includes:"
echo "  - Lambda functions"
echo "  - DynamoDB tables (and all data)"
echo "  - EventBridge rules"
echo "  - SNS topics"
echo "  - IAM roles and policies"
echo "  - CloudWatch log groups"
echo ""

read -p "Are you sure you want to continue? Type 'yes' to confirm: " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Teardown cancelled."
    exit 0
fi

echo ""
echo "Step 1: Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init

echo ""
echo "Step 2: Destroying resources..."
terraform destroy

echo ""
echo "=========================================="
echo "Teardown completed!"
echo "=========================================="
echo ""
echo "Note: Some resources may take a few minutes to fully delete."
echo "      Check the AWS Console to verify all resources are removed."

