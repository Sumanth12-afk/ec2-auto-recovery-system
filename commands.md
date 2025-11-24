# EC2 Auto-Recovery System - Command Reference

This document contains all the commands used for setting up, deploying, testing, and tearing down the EC2 Auto-Recovery System.

## Table of Contents
- [Backend Setup](#backend-setup)
- [Main Infrastructure Deployment](#main-infrastructure-deployment)
- [Lambda Packaging](#lambda-packaging)
- [Testing](#testing)
- [Teardown](#teardown)

---

## Backend Setup

### 1. Navigate to Backend Directory
```powershell
cd infra\terraform\backend
```

### 2. Initialize Terraform (Backend)
```powershell
terraform init
```

### 3. Plan Backend Resources
```powershell
terraform plan
```

### 4. Create Backend S3 Bucket
```powershell
terraform apply
```

### 5. Get Backend Bucket Details
After creation, note the bucket name from the outputs:
```powershell
terraform output
```

---

## Main Infrastructure Deployment

### 1. Navigate to Main Terraform Directory
```powershell
cd ..\..\infra\terraform
# Or from project root:
cd infra\terraform
```

### 2. Initialize Terraform with Backend Configuration
```powershell
terraform init -backend-config="backend/backend-config.tfvars"
```

### 3. Plan Main Infrastructure
```powershell
terraform plan
```

### 4. Deploy Main Infrastructure
```powershell
terraform apply
```

### 5. View Outputs
```powershell
terraform output
```

---

## Lambda Packaging

### 1. Package Lambda Code (Manual)
```powershell
.\scripts\package-lambda.ps1 -OutputFile "infra\terraform\lambda_package.zip"
```

**Note:** This script:
- Copies Lambda code
- Copies prediction engine code
- Installs Python dependencies using Docker (Linux-compatible)
- Creates the deployment zip file

### 2. Update Lambda Function Code (Manual Update)
```powershell
aws lambda update-function-code --function-name ec2-auto-recovery-notifier --zip-file fileb://infra\terraform\lambda_package.zip --region us-east-1
```

**Other Lambda Functions:**
```powershell
# Health Monitor
aws lambda update-function-code --function-name ec2-auto-recovery-health-monitor --zip-file fileb://infra\terraform\lambda_package.zip --region us-east-1

# Predictive Monitor
aws lambda update-function-code --function-name ec2-auto-recovery-predictive-monitor --zip-file fileb://infra\terraform\lambda_package.zip --region us-east-1

# Auto Recovery
aws lambda update-function-code --function-name ec2-auto-recovery-auto-recovery --zip-file fileb://infra\terraform\lambda_package.zip --region us-east-1
```

---

## Testing

### 1. Test Slack Notification
```powershell
.\scripts\test-slack-notification.ps1
```

### 2. Check Lambda Function Logs
```powershell
# Notifier
aws logs tail /aws/lambda/ec2-auto-recovery-notifier --follow --region us-east-1

# Health Monitor
aws logs tail /aws/lambda/ec2-auto-recovery-health-monitor --follow --region us-east-1

# Predictive Monitor
aws logs tail /aws/lambda/ec2-auto-recovery-predictive-monitor --follow --region us-east-1

# Auto Recovery
aws logs tail /aws/lambda/ec2-auto-recovery-auto-recovery --follow --region us-east-1
```

### 3. Invoke Lambda Function Manually
```powershell
# Test Notifier
aws lambda invoke --function-name ec2-auto-recovery-notifier --payload '{"action_taken":"test","instance_id":"i-test123","trigger_cause":"manual_test"}' --region us-east-1 response.json
```

---

## Teardown

### 1. Destroy Main Infrastructure
```powershell
cd infra\terraform
terraform destroy
# Type 'yes' when prompted
```

### 2. Destroy Backend S3 Bucket

#### Step 1: Navigate to Backend Directory
```powershell
cd backend
```

#### Step 2: Delete All Objects and Versions
```powershell
# Delete all objects
aws s3 rm s3://ec2-auto-recovery-terraform-state --recursive --include "*"

# Delete all versions and delete markers
$versions = aws s3api list-object-versions --bucket ec2-auto-recovery-terraform-state --output json | ConvertFrom-Json
if ($versions.Versions) { 
    $versions.Versions | ForEach-Object { 
        aws s3api delete-object --bucket ec2-auto-recovery-terraform-state --key $_.Key --version-id $_.VersionId 
    } 
}
if ($versions.DeleteMarkers) { 
    $versions.DeleteMarkers | ForEach-Object { 
        aws s3api delete-object --bucket ec2-auto-recovery-terraform-state --key $_.Key --version-id $_.VersionId 
    } 
}
```

#### Step 3: Destroy Backend Bucket
```powershell
terraform destroy -auto-approve
```

---

## Quick Reference

### Check Terraform Version
```powershell
terraform --version
```

### Check AWS CLI Configuration
```powershell
aws configure list
aws sts get-caller-identity
```

### List All Lambda Functions
```powershell
aws lambda list-functions --region us-east-1 --query "Functions[?contains(FunctionName, 'ec2-auto-recovery')].FunctionName"
```

### List DynamoDB Tables
```powershell
aws dynamodb list-tables --region us-east-1
```

### List EventBridge Rules
```powershell
aws events list-rules --region us-east-1 --name-prefix "ec2-auto-recovery"
```

### Check S3 Bucket Contents
```powershell
aws s3 ls s3://ec2-auto-recovery-terraform-state --recursive
```

---

## Troubleshooting

### Re-initialize Terraform (if backend changes)
```powershell
terraform init -reconfigure -backend-config="backend/backend-config.tfvars"
```

### Force Unlock Terraform State (if locked)
```powershell
terraform force-unlock <LOCK_ID>
```

### Validate Terraform Configuration
```powershell
terraform validate
```

### Format Terraform Files
```powershell
terraform fmt -recursive
```

---

## Environment Variables

### Required AWS Configuration
```powershell
$env:AWS_PROFILE = "your-profile"
# Or use:
aws configure
```

### Terraform Variables
Variables are defined in:
- `infra/terraform/terraform.tfvars` - Main infrastructure variables
- `infra/terraform/backend/terraform.tfvars` - Backend bucket variables
- `infra/terraform/backend/backend-config.tfvars` - Backend configuration

---

## Notes

- All commands assume you're running from the project root directory unless otherwise specified
- Replace `us-east-1` with your AWS region if different
- The Lambda packaging script requires Docker to be installed and running for Linux-compatible dependencies
- Always verify AWS credentials before running commands: `aws sts get-caller-identity`

