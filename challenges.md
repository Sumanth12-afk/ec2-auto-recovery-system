# EC2 Auto-Recovery System - Challenges & Solutions

This document outlines the challenges encountered during the development and deployment of the EC2 Auto-Recovery System, along with their solutions.

## Table of Contents
- [Lambda Packaging Challenges](#lambda-packaging-challenges)
- [Terraform Backend Configuration](#terraform-backend-configuration)
- [SSM Document Schema Version](#ssm-document-schema-version)
- [Docker and Cross-Platform Dependencies](#docker-and-cross-platform-dependencies)
- [PowerShell Path Handling](#powershell-path-handling)
- [S3 Bucket Deletion with Versioning](#s3-bucket-deletion-with-versioning)

---

## Lambda Packaging Challenges

### Challenge 1: Module Import Errors
**Problem:** Lambda functions were failing with `Runtime.ImportModuleError: No module named 'notifier'`

**Root Cause:** 
- The Lambda package structure didn't match the handler paths
- Initially, the code was packaged with `lambda/` as a parent directory, but handlers expected modules at the root level

**Solution:**
- Modified the packaging script to copy contents of `lambda/` directory directly into the zip root
- Updated handler paths from `lambda.notifier.notification_handler.lambda_handler` to `notifier.notification_handler.lambda_handler`
- Ensured `prediction_engine/` is also copied to the root level of the zip

**Files Affected:**
- `scripts/package-lambda.ps1`
- `infra/terraform/lambda.tf`

---

### Challenge 2: Missing Python Dependencies
**Problem:** Lambda functions failed with `No module named 'pydantic'` and `No module named 'pydantic_core._pydantic_core'`

**Root Cause:**
- Dependencies were not included in the Lambda package
- When installed on Windows, packages were compiled for Windows, not Linux (Lambda's runtime environment)
- Native extensions like `pydantic_core` require Linux-compatible binaries

**Solution:**
- Updated packaging script to install dependencies using Docker with a Linux Python image
- Used `python:3.12-slim` Docker image to install Linux-compatible packages
- Dependencies are now installed into the package before zipping

**Files Affected:**
- `scripts/package-lambda.ps1`

**Key Learning:** Always use Docker or a Linux environment to package Lambda functions with native dependencies.

---

## Terraform Backend Configuration

### Challenge: Dynamic Backend Configuration
**Problem:** Terraform doesn't allow variables in the `backend` block, making it difficult to use dynamic bucket names

**Root Cause:**
- Terraform backend configuration must be static at initialization time
- Variables cannot be used in backend blocks

**Solution:**
- Created a separate `backend/` directory for backend infrastructure
- Used `-backend-config` flag to pass configuration values
- Separated backend bucket creation from backend configuration
- Created `backend-config.tfvars` for backend configuration values

**Files Created:**
- `infra/terraform/backend/backend-bucket.tf` - Creates the S3 bucket
- `infra/terraform/backend/backend-config.tfvars` - Backend configuration
- `infra/terraform/backend/terraform.tfvars` - Bucket creation variables

**Key Learning:** Backend configuration must be static, but you can use separate configurations and `-backend-config` for flexibility.

---

## SSM Document Schema Version

### Challenge: Invalid Schema Version Error
**Problem:** SSM document creation failed with `InvalidDocumentSchemaVersion: 0.3 is not a valid schema version for Command document type`

**Root Cause:**
- Used incorrect schema version `0.3` in SSM YAML documents
- AWS SSM requires schema version `2.2` for Command document type

**Solution:**
- Updated all SSM documents to use `schemaVersion: '2.2'`
- Verified document structure matches AWS SSM requirements

**Files Affected:**
- `src/ssm/restart_services.yml`
- `src/ssm/verify_health.yml`
- `src/ssm/diagnostics.yml`

**Key Learning:** Always check AWS service documentation for correct schema versions and formats.

---

## Docker and Cross-Platform Dependencies

### Challenge: Docker Command Execution in PowerShell
**Problem:** Multiple issues with Docker commands:
1. Lambda Python image requires handler as first argument
2. Paths with spaces causing Docker command failures
3. Empty entrypoint not working correctly

**Root Cause:**
- Lambda Python runtime image (`public.ecr.aws/lambda/python:3.12`) expects a handler function
- PowerShell argument parsing with paths containing spaces
- Empty entrypoint syntax issues

**Solution:**
- Switched from Lambda runtime image to standard `python:3.12-slim` image
- Used `sh -c` to execute pip commands instead of empty entrypoint
- Used PowerShell array syntax for Docker arguments to handle paths with spaces
- Converted Windows paths to forward slashes for Docker container paths

**Files Affected:**
- `scripts/package-lambda.ps1`

**Key Learning:** Use standard Python images for dependency installation, and use array syntax in PowerShell for complex commands.

---

## PowerShell Path Handling

### Challenge: Paths with Spaces in Terraform Provisioners
**Problem:** Terraform `local-exec` provisioner failed with path errors when project directory contained spaces

**Root Cause:**
- Project path: `C:\Users\nalla\OneDrive\Desktop\Projects of BYS\EC2 Availability Monitor & Auto-Recovery System (with Predictive Failure Detection)`
- PowerShell and Terraform had issues with spaces in paths
- Backtick line continuation in PowerShell wasn't working correctly

**Solution:**
- Used absolute paths with Terraform interpolation (`${path.module}`)
- Switched to `cmd /C` interpreter for better path handling
- Used array-based command construction for Docker commands

**Files Affected:**
- `infra/terraform/lambda.tf`
- `scripts/package-lambda.ps1`

**Key Learning:** Always use absolute paths and proper escaping when dealing with paths containing spaces in automation scripts.

---

## S3 Bucket Deletion with Versioning

### Challenge: Cannot Delete S3 Bucket - BucketNotEmpty
**Problem:** S3 bucket deletion failed even after removing all objects: `BucketNotEmpty: The bucket you tried to delete is not empty. You must delete all versions in the bucket.`

**Root Cause:**
- S3 bucket had versioning enabled
- Deleting objects doesn't remove old versions
- Delete markers also need to be removed

**Solution:**
1. List all object versions and delete markers
2. Delete each version individually
3. Delete all delete markers
4. Then delete the bucket

**Commands Used:**
```powershell
# Delete all objects
aws s3 rm s3://bucket-name --recursive

# Delete all versions and delete markers
$versions = aws s3api list-object-versions --bucket bucket-name --output json | ConvertFrom-Json
$versions.Versions | ForEach-Object { aws s3api delete-object --bucket bucket-name --key $_.Key --version-id $_.VersionId }
$versions.DeleteMarkers | ForEach-Object { aws s3api delete-object --bucket bucket-name --key $_.Key --version-id $_.VersionId }
```

**Key Learning:** When versioning is enabled, you must delete all versions and delete markers before the bucket can be deleted.

---

## Additional Challenges

### Challenge: JSON Encoding in PowerShell
**Problem:** Lambda invoke command failed with UTF-8 encoding errors

**Root Cause:**
- PowerShell's `Out-File` adds BOM (Byte Order Mark) to UTF-8 files
- AWS Lambda JSON parser doesn't accept BOM

**Solution:**
- Used `[System.IO.File]::WriteAllText()` with explicit UTF-8 encoding (no BOM)
- Saved JSON to temporary file and used `file://` syntax for AWS CLI

**Files Affected:**
- `scripts/test-slack-notification.ps1`

---

### Challenge: Terraform Provider Lock File
**Problem:** `Error: Inconsistent dependency lock file` when adding `null` provider

**Root Cause:**
- Added `null_resource` for Lambda packaging but didn't update provider lock file

**Solution:**
- Ran `terraform init -upgrade` to update provider lock file

**Key Learning:** Always run `terraform init -upgrade` when adding new providers or changing provider requirements.

---

## Best Practices Learned

1. **Always use Docker for Lambda packaging** when dependencies include native extensions
2. **Test packaging on clean environment** to catch cross-platform issues early
3. **Use separate backend configuration** for flexibility in Terraform
4. **Handle versioned S3 buckets** properly during teardown
5. **Use explicit encoding** when working with JSON files in PowerShell
6. **Validate AWS service schemas** before deployment
7. **Use array syntax** in PowerShell for complex command arguments
8. **Always test Lambda functions** after packaging to catch import errors early

---

## Prevention Strategies

1. **CI/CD Pipeline:** Automate packaging and deployment to catch issues early
2. **Local Testing:** Test Lambda functions locally before deployment
3. **Documentation:** Keep service schemas and requirements documented
4. **Error Handling:** Add proper error handling in scripts
5. **Validation:** Validate Terraform configurations before applying
6. **Monitoring:** Set up CloudWatch alarms for Lambda errors

---

## Future Improvements

1. **Lambda Layers:** Consider using Lambda Layers for common dependencies
2. **Automated Testing:** Add unit tests and integration tests
3. **Infrastructure Testing:** Use Terratest or similar for infrastructure validation
4. **Better Error Messages:** Improve error handling and user feedback
5. **Documentation:** Add inline code documentation
6. **CI/CD:** Set up automated deployment pipeline

