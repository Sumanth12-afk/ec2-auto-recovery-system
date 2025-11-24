# Script to package Lambda code correctly
# Packages lambda/ directory and copies prediction_engine/ into it

param(
    [string]$SourceDir = "src",
    [string]$OutputFile = "infra/terraform/lambda_package.zip"
)


$ErrorActionPreference = "Stop"

Write-Host "Packaging Lambda code..." -ForegroundColor Cyan

# Create temp directory
$tempDir = "lambda_package_temp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    # Copy lambda directory
    Write-Host "Copying lambda directory..." -ForegroundColor Yellow
    Copy-Item -Path "$SourceDir/lambda/*" -Destination $tempDir -Recurse -Force
    
    # Copy prediction_engine directory
    Write-Host "Copying prediction_engine directory..." -ForegroundColor Yellow
    Copy-Item -Path "$SourceDir/prediction_engine" -Destination $tempDir -Recurse -Force
    
    # Install Python dependencies (Linux-compatible for Lambda)
    Write-Host "Installing Python dependencies (Linux-compatible)..." -ForegroundColor Yellow
    if (Test-Path "$SourceDir/lambda/requirements.txt") {
        # Check if Docker is available for Linux-compatible builds
        $dockerAvailable = $false
        try {
            $null = docker --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                $dockerAvailable = $true
            }
        } catch {
            # Docker not available
        }
        
        if ($dockerAvailable) {
            # Use Docker with Lambda Python 3.12 runtime to install dependencies
            Write-Host "Using Docker for Linux-compatible package..." -ForegroundColor Cyan
            $projectRoot = (Resolve-Path "$PSScriptRoot/..").Path
            # Convert Windows paths to forward slashes for Docker container paths
            $requirementsPath = "$SourceDir/lambda/requirements.txt" -replace '\\', '/'
            $tempDirPath = $tempDir -replace '\\', '/'
            # Use standard Python 3.12 image (similar to Lambda runtime)
            # This avoids the Lambda image's handler requirement
            $pipCmd = "pip install -r /var/task/$requirementsPath -t /var/task/$tempDirPath --quiet --disable-pip-version-check"
            $dockerArgs = @(
                "run", "--rm",
                "-v", "${projectRoot}:/var/task",
                "-w", "/var/task",
                "python:3.12-slim",
                "sh", "-c", $pipCmd
            )
            & docker $dockerArgs
        } else {
            Write-Host "WARNING: Docker not available. Installing dependencies may fail for native extensions." -ForegroundColor Yellow
            Write-Host "For best results, install Docker Desktop and rerun this script." -ForegroundColor Yellow
            Write-Host "Attempting installation anyway..." -ForegroundColor Yellow
            pip install -r "$SourceDir/lambda/requirements.txt" -t $tempDir --quiet --disable-pip-version-check
        }
    }
    
    # Remove cache files
    Get-ChildItem -Path $tempDir -Recurse -Include "__pycache__", "*.pyc", "*.dist-info", "*.egg-info" | Remove-Item -Recurse -Force
    
    # Create zip
    Write-Host "Creating zip file..." -ForegroundColor Yellow
    if (Test-Path $OutputFile) {
        Remove-Item -Force $OutputFile
    }
    Compress-Archive -Path "$tempDir/*" -DestinationPath $OutputFile -Force
    
    Write-Host "Lambda package created: $OutputFile" -ForegroundColor Green
} finally {
    # Cleanup
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir
    }
}

