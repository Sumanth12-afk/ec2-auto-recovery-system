# EC2 Availability Monitor & Auto-Recovery System

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/Sumanth12-afk/ec2-auto-recovery-system)

**Repository**: [ec2-auto-recovery-system](https://github.com/Sumanth12-afk/ec2-auto-recovery-system)

## Project Overview

A production-grade, event-driven, serverless automation system that continuously monitors EC2 instances, predicts failures before they occur, and automatically recovers unhealthy instances using AWS-native services.

### What This System Does

This system provides **automated EC2 instance monitoring and recovery** with the following capabilities:

1. **Real-Time Health Monitoring**: Continuously monitors EC2 instances for status check failures, application health issues, and resource constraints (CPU, memory, disk, network).

2. **Predictive Failure Detection**: Analyzes CloudWatch metrics over 7-day periods to detect patterns that indicate potential failures before they occur. Uses statistical heuristics to predict failures with confidence levels (high/medium/low).

3. **Intelligent Auto-Recovery**: Automatically executes recovery actions when failures are detected or predicted, including:
   - Safe instance restarts with EBS snapshots
   - Host migration to healthy hosts
   - Cross-AZ failover
   - EBS volume repair
   - Application-level service restarts via SSM
   - Instance quarantine mode

4. **Multi-Channel Notifications**: Sends detailed incident reports to engineering teams via:
   - Amazon SNS
   - Slack Webhooks
   - Microsoft Teams Webhooks

5. **Configuration Management**: Stores recovery policies, prediction results, and instance configurations in DynamoDB for flexible, per-instance customization.

### Key Technologies

- **AWS Lambda**: Serverless compute for all processing logic
- **EventBridge**: Event-driven orchestration and scheduling
- **CloudWatch**: Metrics collection and logging
- **DynamoDB**: State and configuration storage
- **SSM (Systems Manager)**: Automated recovery actions
- **Terraform**: Infrastructure as Code for deployment

### Architecture Pattern

The system follows an **event-driven, serverless architecture**:
- EventBridge rules trigger Lambda functions based on schedules or EC2 events
- Lambda functions process events, analyze metrics, and execute recovery actions
- DynamoDB stores state, configuration, and history
- SSM documents provide automated recovery scripts
- CloudWatch provides observability and metrics

### Use Cases

- **Production EC2 Instances**: Automatically recover from failures without manual intervention
- **High Availability Requirements**: Minimize downtime through proactive failure detection
- **Cost Optimization**: Prevent unnecessary instance replacements through intelligent recovery
- **Compliance**: Maintain detailed audit logs of all recovery actions

## Features

### 1. Real-Time EC2 Health Monitoring
- Continuous tracking of EC2 System Status Checks
- EC2 Instance Status Checks monitoring
- Application-level health checks (HTTP, TCP)
- CPU utilization, credit balance, throttling indicators
- Memory availability (via CloudWatch Agent)
- Disk usage thresholds (EBS + local)
- Network packet drops, ENA errors

### 2. Predictive Failure Detection
- Statistical analysis of 7-day CloudWatch metric patterns
- Detection of increasing CPUSteal time
- I/O wait spike detection
- Kernel panics or OOM events (CloudWatch Logs)
- Accelerated networking drop detection
- System log anomaly detection
- Memory saturation curve analysis
- File system saturation trend monitoring
- EC2 CPU credit usage pattern analysis (T-family instances)
- Disk queue depth monitoring

**Prediction Confidence Levels:**
- **High confidence**: Failure predicted in next 24 hours
- **Medium confidence**: Failure predicted in 24-72 hours
- **Low confidence**: Early warning (72+ hours)

### 3. Intelligent Auto-Recovery Engine
Recovery actions available:
- **Safe Instance Restart**: Stop → Snapshot EBS → Start → Verify
- **Host Migration**: Migrate to healthy host in same AZ
- **Cross-AZ Failover**: Launch new instance in healthy AZ
- **EBS Volume Repair**: Snapshot → Recreate → Attach
- **App-Level Recovery**: SSM RunCommand for service restarts
- **Instance Quarantine**: Tag and remove from load balancers

### 4. Notifications & Incident Reporting
Supports multiple notification channels:
- Amazon SNS
- Slack Webhook
- Microsoft Teams Webhook

Each notification includes:
- Instance ID, account, region
- Trigger cause (predictive, health, app failure)
- CloudWatch metric chart links
- Remediation steps taken
- Before/after instance state
- Recovery time
- Additional recommendations

### 5. Configuration & State Management
DynamoDB tables for:
- Recovery history logs
- Prediction engine scoring results
- Per-instance policies
- User overrides (disable recovery temporarily)
- Runbook tracking

## Architecture

The system is fully serverless and event-driven:
- **EventBridge**: Triggers monitoring and recovery actions
- **Lambda**: Core processing logic
- **CloudWatch**: Metrics and logging
- **DynamoDB**: State and configuration storage
- **SSM**: Recovery automation documents
- **SNS**: Notification delivery

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- Python 3.12+ (for local testing)
- AWS CLI configured
- EC2 instances with CloudWatch Agent installed (for detailed metrics)

## Installation

### 1. Clone and Setup

```bash
cd "EC2 Availability Monitor & Auto-Recovery System (with Predictive Failure Detection)"
```

### 2. Configure Terraform Variables

Create a `terraform.tfvars` file in `infra/terraform/` (or copy from `terraform.tfvars.example`):

```hcl
aws_region = "us-east-1"
environment = "prod"
terraform_state_bucket = "your-terraform-state-bucket"
terraform_state_key = "ec2-auto-recovery/terraform.tfstate"
terraform_state_region = "us-east-1"

# Slack configuration
slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
slack_channel = "#your-channel"
slack_username = "Your Name"
```

### 3. Configure Backend (Optional - for S3 State Storage)

If you want to use S3 for Terraform state storage:

```powershell
# Navigate to backend folder
cd infra\terraform\backend

# Copy example file
copy backend.tfvars.example backend.tfvars

# Edit backend.tfvars with your bucket name
# Then initialize from terraform directory:
cd ..\..
terraform init -backend-config=backend/backend.tfvars
```

**Create S3 bucket (if it doesn't exist):**
```powershell
aws s3 mb s3://your-terraform-state-bucket-name --region us-east-1
aws s3api put-bucket-versioning --bucket your-terraform-state-bucket-name --versioning-configuration Status=Enabled
```

**Note:** If you skip this step, Terraform will use local state storage (terraform.tfstate file).

### 4. Deploy Infrastructure

```powershell
cd infra\terraform
terraform init
terraform validate
terraform plan
terraform apply
```

Or use the deployment script:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

The deployment script will:
1. Install Python dependencies
2. Initialize Terraform
3. Validate configuration
4. Plan and apply infrastructure

### 4. Enable Monitoring on EC2 Instances

Tag your EC2 instances to enable monitoring:

```bash
aws ec2 create-tags \
  --resources i-1234567890abcdef0 \
  --tags Key=AutoRecovery,Value=enabled
```

### 5. Configure Instance-Specific Policies (Optional)

Update DynamoDB `instance-config` table with per-instance settings:

```python
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ec2-auto-recovery-instance-config')

table.put_item(Item={
    'instance_id': 'i-1234567890abcdef0',
    'recovery_enabled': True,
    'auto_restart': True,
    'app_level_recovery': True,
    'health_endpoint': 'http://localhost:8080/health',
    'notification_channels': ['sns', 'slack']
})
```

## Configuration

### Environment Variables

Lambda functions use the following environment variables (set automatically by Terraform):

- `RECOVERY_EVENTS_TABLE`: DynamoDB table for recovery events
- `PREDICTION_EVENTS_TABLE`: DynamoDB table for predictions
- `INSTANCE_CONFIG_TABLE`: DynamoDB table for instance config
- `SNS_TOPIC_ARN`: SNS topic for notifications
- `SLACK_WEBHOOK_URL`: Slack webhook URL (optional)
- `TEAMS_WEBHOOK_URL`: Teams webhook URL (optional)
- `NOTIFICATION_ENABLED`: Enable/disable notifications

### Prediction Thresholds

Modify thresholds in `config/thresholds/default_thresholds.json` or via environment variables:

- `CPU_STEAL_WARNING`: 5.0%
- `CPU_STEAL_CRITICAL`: 10.0%
- `IOWAIT_WARNING`: 20.0%
- `IOWAIT_CRITICAL`: 40.0%
- `MEMORY_SATURATION_WARNING`: 85.0%
- `MEMORY_SATURATION_CRITICAL`: 95.0%
- `DISK_USAGE_WARNING`: 80.0%
- `DISK_USAGE_CRITICAL`: 90.0%

## Usage

### Monitoring

The system automatically:
1. Runs predictive monitoring on a schedule (default: hourly)
2. Monitors EC2 status check events via EventBridge
3. Analyzes CloudWatch metrics for failure patterns
4. Triggers recovery actions when needed

### Manual Recovery Trigger

You can manually trigger recovery for an instance:

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='ec2-auto-recovery-auto-recovery',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'instance_id': 'i-1234567890abcdef0',
        'trigger_type': 'manual'
    })
)
```

### Viewing Recovery History

Query DynamoDB for recovery events:

```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ec2-auto-recovery-recovery-events')

response = table.query(
    KeyConditionExpression=Key('instance_id').eq('i-1234567890abcdef0')
)

for item in response['Items']:
    print(f"{item['timestamp']}: {item['action_taken']} - {item['status']}")
```

## Local Testing

Use the local debug script to test Lambda functions:

```bash
chmod +x scripts/local_debug.sh
./scripts/local_debug.sh
```

## Monitoring and Logs

### CloudWatch Logs

All Lambda functions write structured JSON logs to CloudWatch:
- `/aws/lambda/ec2-auto-recovery-predictive-monitor`
- `/aws/lambda/ec2-auto-recovery-health-monitor`
- `/aws/lambda/ec2-auto-recovery-auto-recovery`
- `/aws/lambda/ec2-auto-recovery-notifier`

### CloudWatch Metrics

Custom metrics are published to namespace: `EC2/AutoRecovery`

### DynamoDB Tables

- `ec2-auto-recovery-recovery-events`: Recovery action history
- `ec2-auto-recovery-prediction-events`: Prediction results (with TTL)
- `ec2-auto-recovery-instance-config`: Per-instance configuration

## Testing Slack Notifications

To test your Slack notification setup:

**Windows (PowerShell):**
```powershell
.\scripts\test-slack-notification.ps1
```

**Linux/Mac (Bash):**
```bash
chmod +x scripts/test-slack-notification.sh
./scripts/test-slack-notification.sh
```

This will send a test notification to your Slack channel (`#team-collab`) to verify the integration is working.

## Troubleshooting

### Lambda Function Errors

1. Check CloudWatch Logs for detailed error messages
2. Verify IAM permissions are correctly configured
3. Ensure DynamoDB tables exist and are accessible
4. Check that EC2 instances have required tags

### Recovery Not Triggering

1. Verify instance has `AutoRecovery=enabled` tag
2. Check instance config in DynamoDB (recovery may be disabled)
3. Review EventBridge rules are active
4. Check Lambda function logs for errors

### Notifications Not Sending

1. Verify SNS topic exists and has subscriptions
2. Check webhook URLs are correct (for Slack/Teams)
3. Ensure `NOTIFICATION_ENABLED` environment variable is `true`
4. Review notifier Lambda logs

## Cost Optimization

- DynamoDB uses on-demand billing (pay per request)
- Lambda functions use minimal memory (512MB default)
- CloudWatch Logs retention: 14-30 days
- Prediction events have TTL (30 days) for automatic cleanup

## Security

- IAM roles follow least-privilege principle
- All Lambda functions use VPC endpoints (if configured)
- Sensitive data (webhooks) stored as environment variables
- DynamoDB tables have point-in-time recovery enabled

## Teardown

To remove all resources:

```bash
chmod +x scripts/teardown.sh
./scripts/teardown.sh
```

**Warning**: This will delete all DynamoDB tables and their data!

## Project Structure

```
/
├─ src/                          # Source code directory
│  ├─ lambda/                    # Lambda function source code
│  │  ├─ monitor/               # Monitoring Lambda functions
│  │  ├─ auto_recovery/         # Auto-recovery Lambda functions
│  │  ├─ notifier/              # Notification Lambda functions
│  │  └─ utils/                 # Shared utility modules
│  ├─ ssm/                      # AWS Systems Manager documents
│  └─ prediction_engine/        # Predictive failure detection engine
│
├─ infra/                       # Infrastructure as Code
│  └─ terraform/               # Terraform configuration files
│     ├─ main.tf                # Main Terraform configuration
│     ├─ variables.tf          # Input variable definitions
│     ├─ outputs.tf            # Output value definitions
│     ├─ dynamodb.tf            # DynamoDB table resources
│     ├─ eventbridge.tf         # EventBridge rules and targets
│     ├─ lambda.tf              # Lambda function resources
│     ├─ sns.tf                 # SNS topic resources
│     ├─ ssm.tf                 # SSM document resources
│     ├─ iam.tf                 # IAM roles and policies
│     └─ backend/               # Terraform backend configuration
│
├─ scripts/                     # Automation and utility scripts
│  ├─ package-lambda.ps1        # PowerShell script to package Lambda code
│  ├─ test-slack-notification.ps1 # Test Slack notification script
│  ├─ deploy.sh                 # Deployment automation script
│  └─ teardown.sh               # Teardown automation script
│
├─ docs/                        # Documentation directory
├─ README.md                    # This file - project documentation
├─ commands.md                  # Command reference guide
└─ challenges.md                # Challenges faced and solutions
```

## Detailed File Explanations

### Source Code (`src/`)

#### Lambda Functions (`src/lambda/`)

**`monitor/predictive_monitor.py`**
- **Purpose**: Lambda function that runs on a schedule to analyze CloudWatch metrics and predict potential failures
- **Why**: Enables proactive failure detection before instances actually fail
- **Triggers**: EventBridge scheduled rule (default: hourly)
- **Key Features**: 
  - Fetches 7-day metric history from CloudWatch
  - Calls prediction engine to analyze patterns
  - Stores predictions in DynamoDB
  - Publishes high-confidence predictions to EventBridge

**`monitor/health_monitor.py`**
- **Purpose**: Real-time health monitoring Lambda triggered by EC2 status change events
- **Why**: Provides immediate response to EC2 status check failures
- **Triggers**: EventBridge rule for EC2 instance state/status changes
- **Key Features**:
  - Monitors System Status Checks and Instance Status Checks
  - Checks application-level health endpoints
  - Triggers recovery for failed status checks

**`auto_recovery/recovery_engine.py`**
- **Purpose**: Main recovery orchestration Lambda that executes recovery actions
- **Why**: Centralizes all recovery logic and decision-making
- **Triggers**: EventBridge events from predictive monitor or health monitor
- **Key Features**:
  - Implements recovery action selection logic
  - Executes recovery actions (restart, migration, failover, etc.)
  - Verifies recovery success
  - Logs all recovery events to DynamoDB
  - Triggers notifications

**`notifier/notification_handler.py`**
- **Purpose**: Sends notifications to SNS, Slack, and Microsoft Teams
- **Why**: Keeps engineering teams informed of recovery actions and failures
- **Triggers**: EventBridge events after recovery completion
- **Key Features**:
  - Formats incident reports with detailed information
  - Sends to multiple notification channels
  - Includes CloudWatch dashboard links
  - Provides recovery recommendations

**`utils/aws_client.py`**
- **Purpose**: Centralized AWS service client initialization
- **Why**: Ensures consistent client configuration and reduces code duplication
- **Key Features**: 
  - Lazy initialization of boto3 clients
  - Consistent error handling
  - Region configuration

**`utils/logger.py`**
- **Purpose**: Structured JSON logging utility
- **Why**: Enables better log analysis and CloudWatch Insights queries
- **Key Features**:
  - JSON-formatted logs
  - Contextual information (instance_id, request_id, etc.)
  - Log levels (DEBUG, INFO, WARNING, ERROR)

**`utils/config.py`**
- **Purpose**: Pydantic-based configuration models
- **Why**: Type-safe configuration with validation
- **Key Features**:
  - Environment variable parsing
  - Default values
  - Type validation
  - Models for: NotificationConfig, RecoveryPolicy, PredictionThresholds

**`utils/dynamodb_helpers.py`**
- **Purpose**: Helper functions for DynamoDB operations
- **Why**: Simplifies DynamoDB interactions and reduces boilerplate
- **Key Features**:
  - Save recovery events
  - Save prediction events
  - Get instance configuration
  - Query recovery history

**`utils/requirements.txt`**
- **Purpose**: Python package dependencies for Lambda functions
- **Why**: Ensures all required packages are included in Lambda deployment
- **Key Dependencies**: boto3, pydantic

#### SSM Documents (`src/ssm/`)

**`restart_services.yml`**
- **Purpose**: AWS Systems Manager document to restart application services
- **Why**: Enables automated service restarts without SSH access
- **Usage**: Called by recovery engine for app-level recovery
- **Features**: Supports systemd, init.d, and Docker services

**`verify_health.yml`**
- **Purpose**: SSM document to verify instance health after recovery
- **Why**: Validates that recovery actions were successful
- **Usage**: Called after recovery actions to confirm instance is healthy
- **Features**: Checks health endpoint and system resources (CPU, memory, disk)

**`diagnostics.yml`**
- **Purpose**: SSM document for system diagnostics
- **Why**: Collects diagnostic information when issues are detected
- **Usage**: Can be run manually or triggered by recovery engine
- **Features**: Collects system info, CPU, memory, disk, network, and logs

#### Prediction Engine (`src/prediction_engine/`)

**`metric_analysis.py`**
- **Purpose**: Analyzes CloudWatch metrics for failure patterns
- **Why**: Detects anomalies and trends that indicate potential failures
- **Key Features**:
  - CPU steal time analysis
  - I/O wait spike detection
  - Memory saturation curve analysis
  - Disk usage trend monitoring
  - CPU credit balance analysis

**`anomaly_scoring.py`**
- **Purpose**: Scores detected anomalies to determine prediction confidence
- **Why**: Provides confidence levels (high/medium/low) for predictions
- **Key Features**:
  - Combines multiple anomaly signals
  - Calculates confidence scores
  - Stores predictions in DynamoDB

**`prediction_rules.json`**
- **Purpose**: Configuration file for prediction rules and thresholds
- **Why**: Allows easy adjustment of prediction sensitivity without code changes
- **Contains**: Thresholds for various metrics and anomaly detection rules

### Infrastructure (`infra/terraform/`)

**`main.tf`**
- **Purpose**: Main Terraform configuration file
- **Why**: Defines provider requirements and Terraform settings
- **Contains**: AWS provider configuration, Terraform version requirements

**`variables.tf`**
- **Purpose**: Defines all input variables for the Terraform configuration
- **Why**: Makes the configuration reusable and configurable
- **Key Variables**: AWS region, environment, notification URLs, thresholds

**`outputs.tf`**
- **Purpose**: Defines output values after Terraform apply
- **Why**: Provides important resource information (ARNs, names, etc.)
- **Outputs**: Lambda function ARNs, DynamoDB table names, EventBridge rule ARNs

**`dynamodb.tf`**
- **Purpose**: Creates DynamoDB tables for state and configuration storage
- **Why**: Provides persistent storage for recovery history, predictions, and config
- **Tables Created**:
  - `recovery_events`: Recovery action history
  - `prediction_events`: Prediction results (with TTL)
  - `instance_config`: Per-instance configuration

**`eventbridge.tf`**
- **Purpose**: Creates EventBridge rules and targets
- **Why**: Orchestrates the event-driven workflow
- **Rules Created**:
  - Scheduled rule for predictive monitoring
  - EC2 status change rule for health monitoring
  - Recovery trigger rules
  - Notification trigger rules

**`lambda.tf`**
- **Purpose**: Creates Lambda function resources
- **Why**: Deploys all Lambda functions with proper configuration
- **Features**: 
  - Packages Lambda code
  - Sets environment variables
  - Configures IAM roles
  - Sets memory, timeout, and other settings

**`sns.tf`**
- **Purpose**: Creates SNS topic for notifications
- **Why**: Provides AWS-native notification channel
- **Features**: Optional SNS topic creation (can be disabled)

**`ssm.tf`**
- **Purpose**: Creates SSM documents from YAML files
- **Why**: Deploys automation documents for recovery actions
- **Documents**: restart_services, verify_health, diagnostics

**`iam.tf`**
- **Purpose**: Creates IAM roles and policies for Lambda functions
- **Why**: Provides least-privilege permissions for Lambda execution
- **Features**: 
  - Lambda execution role
  - Granular permissions for EC2, CloudWatch, DynamoDB, SSM, SNS

**`terraform.tfvars`**
- **Purpose**: User-specific variable values
- **Why**: Allows customization without modifying code
- **Contains**: Region, environment, webhook URLs, channel names

**`backend/backend.tf`**
- **Purpose**: Terraform backend configuration for S3 state storage
- **Why**: Enables remote state storage for team collaboration
- **Note**: Values provided via `-backend-config` flag

**`backend/backend-bucket.tf`**
- **Purpose**: Creates the S3 bucket for Terraform state
- **Why**: Provides the storage bucket for remote state
- **Features**: Versioning, encryption, lifecycle rules

**`backend/backend-config.tfvars`**
- **Purpose**: Backend configuration values (bucket name, key, region)
- **Why**: Separates backend config from bucket creation
- **Contains**: S3 bucket name, state file key, region

### Scripts (`scripts/`)

**`package-lambda.ps1`**
- **Purpose**: Packages Lambda code with dependencies for deployment
- **Why**: Ensures Linux-compatible dependencies are included
- **Features**:
  - Copies Lambda and prediction engine code
  - Uses Docker to install Linux-compatible Python packages
  - Creates deployment zip file
  - Handles paths with spaces

**`test-slack-notification.ps1`**
- **Purpose**: Tests Slack notification integration
- **Why**: Verifies notification setup without triggering actual recovery
- **Features**: Invokes notifier Lambda with test payload

**`test-slack-notification.sh`**
- **Purpose**: Bash version of Slack notification test script
- **Why**: Provides cross-platform testing capability

**`deploy.sh`**
- **Purpose**: Automated deployment script
- **Why**: Simplifies deployment process
- **Features**: Initializes Terraform, validates, plans, and applies

**`teardown.sh`**
- **Purpose**: Automated teardown script
- **Why**: Simplifies resource cleanup
- **Features**: Destroys all Terraform-managed resources

**`local_debug.sh`**
- **Purpose**: Local debugging script for Lambda functions
- **Why**: Enables testing Lambda functions locally before deployment

### Documentation Files

**`README.md`**
- **Purpose**: Main project documentation
- **Why**: Provides setup, usage, and configuration instructions

**`commands.md`**
- **Purpose**: Command reference guide
- **Why**: Quick reference for all commands used in the project

**`challenges.md`**
- **Purpose**: Documents challenges faced and solutions
- **Why**: Helps future developers understand issues and solutions

**`.gitignore`**
- **Purpose**: Git ignore patterns
- **Why**: Prevents committing sensitive files and build artifacts
- **Ignores**: Terraform state, `.terraform/`, zip files, sensitive configs

**`requirements.txt`**
- **Purpose**: Root-level Python dependencies
- **Why**: For local development and testing

## License

This project is provided as-is for production use.

## Support

For issues or questions:
1. Check CloudWatch Logs for detailed error messages
2. Review DynamoDB tables for configuration issues
3. Verify EventBridge rules are active
4. Ensure all prerequisites are met

