# Terraform Backend Configuration Documentation
# ============================================
# 
# Note: The backend block must be defined in main.tf (Terraform requirement)
# This folder contains the backend configuration values (backend.tfvars)
#
# Usage:
# ------
# 1. Copy backend.tfvars.example to backend.tfvars
# 2. Edit backend.tfvars with your bucket name
# 3. Initialize: terraform init -backend-config=backend/backend.tfvars
#
# The backend block in main.tf will use values from backend/backend.tfvars

