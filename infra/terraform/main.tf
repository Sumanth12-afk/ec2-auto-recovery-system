terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration values are in backend/backend-config.tfvars
  # Initialize with: terraform init -backend-config=backend/backend-config.tfvars
  # Or use local state by skipping backend config
  backend "s3" {
    # Partial configuration - values provided via backend/backend.tfvars
    # See backend/README.md for setup instructions
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "EC2-Auto-Recovery"
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}

locals {
  project_name = "ec2-auto-recovery"
  
  common_tags = {
    Project     = local.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

