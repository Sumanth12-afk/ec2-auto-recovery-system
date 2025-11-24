# Bootstrap: Create S3 bucket for Terraform state storage
# This should be applied FIRST before initializing the main Terraform backend
# Run: terraform init && terraform apply (in this backend directory)

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Use local state for bootstrap (chicken-egg problem)
  # After bucket is created, main Terraform will use S3 backend
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for the backend bucket"
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  type        = string
  default     = "ec2-auto-recovery-terraform-state"
}

variable "enable_versioning" {
  description = "Enable versioning on the S3 bucket"
  type        = bool
  default     = true
}

variable "enable_encryption" {
  description = "Enable server-side encryption"
  type        = bool
  default     = true
}

# S3 bucket for Terraform state
resource "aws_s3_bucket" "terraform_state" {
  bucket = var.bucket_name

  tags = {
    Name        = "Terraform State Bucket"
    Purpose     = "EC2 Auto-Recovery Terraform State"
    ManagedBy   = "Terraform"
    Environment = "shared"
  }
}

# Enable versioning
resource "aws_s3_bucket_versioning" "terraform_state" {
  count  = var.enable_versioning ? 1 : 0
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  count  = var.enable_encryption ? 1 : 0
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets  = true
}

# Lifecycle rule to prevent accidental deletion
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "prevent-deletion"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

output "bucket_name" {
  description = "Name of the created S3 bucket"
  value       = aws_s3_bucket.terraform_state.id
}

output "bucket_arn" {
  description = "ARN of the created S3 bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

