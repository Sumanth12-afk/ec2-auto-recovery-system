# Terraform Backend Configuration

This folder contains the backend configuration for Terraform state storage.

## Files

- `backend-bucket.tf` - Creates the S3 bucket for Terraform state (apply this FIRST)
- `terraform.tfvars` - Single configuration file for BOTH bucket creation and backend config (automatically loaded)
- `terraform.tfvars.example` - Example configuration file
- `backend.tf` - Backend block documentation

## Setup Workflow

### Step 1: Configure Backend (Single File)

1. **Copy and edit the configuration file:**
   ```powershell
   cd infra\terraform\backend
   copy terraform.tfvars.example terraform.tfvars
   notepad terraform.tfvars
   ```

2. **Edit `terraform.tfvars` - this file is for bucket creation:**
   ```hcl
   aws_region = "us-east-1"
   bucket_name = "ec2-auto-recovery-terraform-state"
   enable_versioning = true
   enable_encryption = true
   ```

3. **Create backend config file (for main Terraform):**
   ```powershell
   copy backend-config.tfvars.example backend-config.tfvars
   notepad backend-config.tfvars
   ```
   
   Make sure values match:
   ```hcl
   bucket = "ec2-auto-recovery-terraform-state"  # Must match bucket_name
   key    = "ec2-auto-recovery/terraform.tfstate"
   region = "us-east-1"  # Must match aws_region
   ```

### Step 2: Create the S3 Bucket (Using Terraform)

```powershell
# Initialize and create the bucket
# terraform.tfvars is automatically loaded - no need for -var-file flag!
terraform init
terraform plan
terraform apply
```

This creates the S3 bucket with versioning and encryption enabled.

### Step 3: Initialize Main Terraform with Backend

```powershell
cd ..\..
terraform init -backend-config=backend/backend-config.tfvars
```

### Step 3: Deploy Main Infrastructure

```powershell
terraform validate
terraform plan
terraform apply
```

## Cleanup / Deletion

To delete everything (including the backend bucket):

1. **Destroy main infrastructure:**
   ```powershell
   cd infra\terraform
   terraform destroy
   ```

2. **Destroy the backend bucket:**
   ```powershell
   cd backend
   terraform destroy
   ```

## Notes

- The backend bucket is created separately to avoid chicken-egg problem
- Backend bucket uses local state initially, then main Terraform uses S3 backend
- Keep `terraform.tfvars` out of version control if needed
- The bucket has lifecycle rules to prevent accidental deletion

