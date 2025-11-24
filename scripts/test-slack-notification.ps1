# Test Slack Notification Script
# This script invokes the notifier Lambda function to send a test notification to Slack

param(
    [string]$InstanceId = "i-test1234567890",
    [string]$Region = "us-east-1"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Testing Slack Notification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get AWS account ID
$accountId = (aws sts get-caller-identity --query Account --output text)
if (-not $accountId) {
    Write-Host "Error: AWS credentials not configured. Please run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "AWS Account: $accountId" -ForegroundColor Green
Write-Host "Region: $Region" -ForegroundColor Green
Write-Host "Instance ID: $InstanceId" -ForegroundColor Green
Write-Host ""

# Create test payload
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$payload = @{
    instance_id = $InstanceId
    trigger_cause = "test"
    action_taken = "test_notification"
    result = @{
        success = $true
        timestamp = $timestamp
        message = "This is a test notification from EC2 Auto-Recovery System"
    }
} | ConvertTo-Json -Depth 10 -Compress

Write-Host "Payload:" -ForegroundColor Yellow
Write-Host $payload -ForegroundColor Gray
Write-Host ""

# Save payload to temporary file (UTF-8 without BOM)
$payloadFile = Join-Path $PSScriptRoot "test-payload.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($payloadFile, $payload, $utf8NoBom)

Write-Host "Invoking notifier Lambda function..." -ForegroundColor Yellow

# Get absolute path for file:// syntax
$absolutePayloadFile = (Resolve-Path $payloadFile).Path

# Invoke Lambda function using file:// syntax
$response = aws lambda invoke `
    --function-name "ec2-auto-recovery-notifier" `
    --payload "file://$absolutePayloadFile" `
    --region $Region `
    --cli-binary-format raw-in-base64-out `
    response.json 2>&1

# Clean up payload file
Remove-Item $payloadFile -ErrorAction SilentlyContinue

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "Notification sent successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check your Slack channel: #team-collab" -ForegroundColor Cyan
    Write-Host ""
    
    # Show response
    if (Test-Path "response.json") {
        $responseContent = Get-Content "response.json" -Raw | ConvertFrom-Json
        Write-Host "Lambda Response:" -ForegroundColor Yellow
        Write-Host ($responseContent | ConvertTo-Json -Depth 5) -ForegroundColor Gray
        Remove-Item "response.json" -ErrorAction SilentlyContinue
    }
} else {
    Write-Host ""
    Write-Host "Error: Failed to invoke Lambda function" -ForegroundColor Red
    Write-Host $response -ForegroundColor Red
    exit 1
}

