# EC2 Auto-Recovery System

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/Sumanth12-afk/ec2-auto-recovery-system)

**Repository**: [ec2-auto-recovery-system](https://github.com/Sumanth12-afk/ec2-auto-recovery-system)

## Overview

Production-grade, serverless EC2 monitoring and auto-recovery system with predictive failure detection. Automatically monitors EC2 instances, predicts failures before they occur, and executes intelligent recovery actions using AWS-native services.

## Features

- **Real-Time Health Monitoring**: EC2 status checks, application health, CPU/memory/disk monitoring
- **Predictive Failure Detection**: 7-day CloudWatch metric analysis with confidence scoring (high/medium/low)
- **Intelligent Auto-Recovery**: Safe restarts, host migration, cross-AZ failover, EBS repair, app-level recovery
- **Multi-Channel Notifications**: SNS, Slack, and Microsoft Teams webhooks
- **Fully Serverless**: EventBridge, Lambda, DynamoDB, CloudWatch, SSM

## Architecture

```
EC2 Instances → CloudWatch → EventBridge → Lambda Functions → DynamoDB
                                              ↓
                                    Auto-Recovery → SSM → EC2
                                              ↓
                                    Notifier → SNS/Slack/Teams
```

**Components:**
- **EventBridge**: Event orchestration and scheduling
- **Lambda Functions**: Predictive Monitor, Health Monitor, Auto-Recovery Engine, Notifier
- **DynamoDB**: Recovery events, predictions, instance config
- **SSM**: Automated recovery scripts
- **CloudWatch**: Metrics and logging

## Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured
- Docker (for Lambda packaging)

### Installation

1. **Configure Variables**

   Copy `infra/terraform/terraform.tfvars.example` to `infra/terraform/terraform.tfvars` and update:

   ```hcl
   aws_region = "us-east-1"
   environment = "prod"
   slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   slack_channel = "#your-channel"
   slack_username = "Your Name"
   ```

2. **Setup Backend (Optional)**

   ```powershell
   cd infra\terraform\backend
   terraform init
   terraform apply
   ```

3. **Deploy Infrastructure**

   ```powershell
   cd infra\terraform
   terraform init -backend-config="backend/backend-config.tfvars"
   terraform plan
   terraform apply
   ```

4. **Package Lambda Functions**

   ```powershell
   .\scripts\package-lambda.ps1 -OutputFile "infra\terraform\lambda_package.zip"
   ```

5. **Tag EC2 Instances**

   ```bash
   aws ec2 create-tags \
     --resources i-1234567890abcdef0 \
     --tags Key=AutoRecovery,Value=enabled
   ```

## Configuration

### Environment Variables (Set by Terraform)

- `RECOVERY_EVENTS_TABLE`: DynamoDB table for recovery history
- `PREDICTION_EVENTS_TABLE`: DynamoDB table for predictions
- `INSTANCE_CONFIG_TABLE`: DynamoDB table for instance config
- `SLACK_WEBHOOK_URL`: Slack webhook URL
- `TEAMS_WEBHOOK_URL`: Teams webhook URL (optional)
- `SNS_TOPIC_ARN`: SNS topic ARN (optional)

### Instance Configuration

Configure per-instance policies in DynamoDB `instance_config` table:

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
    'notification_channels': ['slack', 'sns']
})
```

## Usage

### Testing Notifications

**Windows:**
```powershell
.\scripts\test-slack-notification.ps1
```

**Linux/Mac:**
```bash
./scripts/test-slack-notification.sh
```

### View Recovery History

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

### Manual Recovery Trigger

```python
import boto3
import json

lambda_client = boto3.client('lambda')

lambda_client.invoke(
    FunctionName='ec2-auto-recovery-auto-recovery',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'instance_id': 'i-1234567890abcdef0',
        'trigger_type': 'manual'
    })
)
```

## Health Checking

The system uses **AWS Systems Manager (SSM) documents** (YAML files) to perform health checks and recovery actions on EC2 instances.

### SSM Documents

Three SSM documents are deployed to handle different aspects of health checking and recovery:

1. **`verify_health.yml`** - Health Verification
   - Checks application health endpoint (HTTP status)
   - Validates system resources (CPU, memory, disk usage)
   - Used after recovery actions to confirm instance is healthy
   - Configurable health endpoint URL (default: `http://localhost:8080/health`)

2. **`restart_services.yml`** - Service Restart Automation
   - Restarts application services via systemd, init.d, or Docker
   - Used for app-level recovery when services fail
   - Supports multiple service management systems

3. **`diagnostics.yml`** - System Diagnostics
   - Collects system information (CPU, memory, disk, network)
   - Gathers recent system logs
   - Used for troubleshooting and diagnostics

### How Health Checking Works

1. **Real-Time Monitoring**: Health Monitor Lambda checks EC2 status checks via CloudWatch
2. **Application Health**: If configured, checks application health endpoint via HTTP
3. **Post-Recovery Verification**: After recovery actions, SSM `verify_health` document is executed to confirm instance is healthy
4. **Resource Validation**: Verifies CPU, memory, and disk usage are within acceptable thresholds

### Configuration

Set health endpoint in instance configuration:

```python
table.put_item(Item={
    'instance_id': 'i-1234567890abcdef0',
    'health_endpoint': 'http://localhost:8080/health',  # Your app health endpoint
    'app_level_recovery': True  # Enable SSM-based recovery
})
```

## Monitoring

### CloudWatch Logs

- `/aws/lambda/ec2-auto-recovery-predictive-monitor`
- `/aws/lambda/ec2-auto-recovery-health-monitor`
- `/aws/lambda/ec2-auto-recovery-auto-recovery`
- `/aws/lambda/ec2-auto-recovery-notifier`

### DynamoDB Tables

- `ec2-auto-recovery-recovery-events`: Recovery action history
- `ec2-auto-recovery-prediction-events`: Prediction results (TTL: 30 days)
- `ec2-auto-recovery-instance-config`: Per-instance configuration

## Project Structure

```
/
├─ src/                          # Source code directory
│  ├─ lambda/                    # Lambda function source code
│  │  ├─ monitor/               # Monitoring Lambda functions
│  │  │  ├─ predictive_monitor.py    # Predictive failure detection
│  │  │  └─ health_monitor.py         # Real-time health monitoring
│  │  ├─ auto_recovery/         # Auto-recovery Lambda functions
│  │  │  └─ recovery_engine.py        # Main recovery orchestration
│  │  ├─ notifier/              # Notification Lambda functions
│  │  │  └─ notification_handler.py   # SNS/Slack/Teams notifications
│  │  └─ utils/                 # Shared utility modules
│  │     ├─ aws_client.py       # AWS service clients
│  │     ├─ logger.py           # Structured JSON logging
│  │     ├─ config.py           # Pydantic configuration models
│  │     ├─ dynamodb_helpers.py # DynamoDB helper functions
│  │     └─ requirements.txt    # Python dependencies
│  ├─ ssm/                      # AWS Systems Manager documents
│  │  ├─ restart_services.yml    # Service restart automation
│  │  ├─ verify_health.yml      # Health verification
│  │  └─ diagnostics.yml       # System diagnostics
│  └─ prediction_engine/        # Predictive failure detection engine
│     ├─ metric_analysis.py     # CloudWatch metric pattern analysis
│     ├─ anomaly_scoring.py     # Anomaly detection and scoring
│     └─ prediction_rules.json # Prediction rules and thresholds
│
├─ infra/                       # Infrastructure as Code
│  └─ terraform/               # Terraform configuration files
│     ├─ main.tf                # Main Terraform configuration
│     ├─ variables.tf           # Input variable definitions
│     ├─ outputs.tf             # Output value definitions
│     ├─ dynamodb.tf             # DynamoDB table resources
│     ├─ eventbridge.tf          # EventBridge rules and targets
│     ├─ lambda.tf              # Lambda function resources
│     ├─ sns.tf                 # SNS topic resources
│     ├─ ssm.tf                 # SSM document resources
│     ├─ iam.tf                 # IAM roles and policies
│     ├─ terraform.tfvars       # Variable values (user-specific)
│     └─ backend/               # Terraform backend configuration
│        ├─ backend.tf           # Backend S3 configuration
│        ├─ backend-bucket.tf    # S3 bucket creation for state
│        └─ backend-config.tfvars # Backend configuration values
│
├─ scripts/                     # Automation and utility scripts
│  ├─ package-lambda.ps1        # PowerShell script to package Lambda code
│  ├─ test-slack-notification.ps1 # Test Slack notification (PowerShell)
│  ├─ test-slack-notification.sh # Test Slack notification (Bash)
│  ├─ deploy.sh                 # Deployment automation script
│  ├─ teardown.sh               # Teardown automation script
│  └─ local_debug.sh            # Local debugging script
│
├─ config/                      # Configuration files
│  ├─ policies/                 # Recovery policy templates
│  └─ thresholds/               # Prediction threshold configurations
│
├─ docs/                        # Documentation directory
├─ .gitignore                   # Git ignore patterns
├─ requirements.txt             # Python dependencies (root level)
├─ README.md                    # This file - project documentation
├─ commands.md                  # Command reference guide
├─ challenges.md                # Challenges faced and solutions
├─ architecture-diagram.xml     # Architecture diagram specification
└─ sora-architecture-command.xml # Sora diagram generation command
```

## Troubleshooting

### Lambda Errors
- Check CloudWatch Logs for detailed errors
- Verify IAM permissions
- Ensure DynamoDB tables exist

### Recovery Not Triggering
- Verify instance has `AutoRecovery=enabled` tag
- Check instance config in DynamoDB
- Review EventBridge rules are active

### Notifications Not Sending
- Verify webhook URLs are correct
- Check `NOTIFICATION_ENABLED` environment variable
- Review notifier Lambda logs

## Teardown

```powershell
cd infra\terraform
terraform destroy
```

**Note**: To delete backend S3 bucket, see `commands.md` for detailed steps.

## Documentation

- **[commands.md](commands.md)**: Command reference guide
- **[challenges.md](challenges.md)**: Challenges faced and solutions
- **[architecture-diagram.xml](architecture-diagram.xml)**: Architecture diagram specification

## License

This project is provided as-is for production use.

## Support

For issues:
1. Check CloudWatch Logs
2. Review DynamoDB tables
3. Verify EventBridge rules
4. See `challenges.md` for common issues
