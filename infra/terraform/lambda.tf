# Package Lambda code using script (combines lambda/ and prediction_engine/)
resource "null_resource" "package_lambda" {
  triggers = {
    lambda_code = sha256(join("", [
      for f in fileset("${path.module}/../../src/lambda", "**") : filesha256("${path.module}/../../src/lambda/${f}")
    ]))
    prediction_code = sha256(join("", [
      for f in fileset("${path.module}/../../src/prediction_engine", "**") : filesha256("${path.module}/../../src/prediction_engine/${f}")
    ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd "${path.module}/../.." && powershell -ExecutionPolicy Bypass -File scripts/package-lambda.ps1 -OutputFile infra/terraform/lambda_package.zip
    EOT
    interpreter = ["cmd", "/C"]
  }
}

# Use the packaged file
locals {
  lambda_package_path = "${path.module}/lambda_package.zip"
}

# Predictive Monitor Lambda
resource "aws_lambda_function" "predictive_monitor" {
  filename         = local.lambda_package_path
  function_name    = "${var.project_name}-predictive-monitor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "monitor.predictive_monitor.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  source_code_hash = filebase64sha256(local.lambda_package_path)

  environment {
    variables = {
      RECOVERY_EVENTS_TABLE      = aws_dynamodb_table.recovery_events.name
      PREDICTION_EVENTS_TABLE    = aws_dynamodb_table.prediction_events.name
      INSTANCE_CONFIG_TABLE      = aws_dynamodb_table.instance_config.name
      METRIC_NAMESPACE           = "EC2/AutoRecovery"
      PREDICTION_LOOKBACK_HOURS  = var.prediction_lookback_hours
      HIGH_CONFIDENCE_THRESHOLD  = var.high_confidence_threshold
      MEDIUM_CONFIDENCE_THRESHOLD = var.medium_confidence_threshold
      NOTIFICATION_ENABLED       = var.enable_notifications
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-predictive-monitor"
  })
}

# Health Monitor Lambda
resource "aws_lambda_function" "health_monitor" {
  filename         = local.lambda_package_path
  function_name    = "${var.project_name}-health-monitor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "monitor.health_monitor.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size
  
  source_code_hash = filebase64sha256(local.lambda_package_path)

  environment {
    variables = {
      RECOVERY_EVENTS_TABLE      = aws_dynamodb_table.recovery_events.name
      PREDICTION_EVENTS_TABLE    = aws_dynamodb_table.prediction_events.name
      INSTANCE_CONFIG_TABLE      = aws_dynamodb_table.instance_config.name
      NOTIFICATION_ENABLED       = var.enable_notifications
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-health-monitor"
  })
}

# Auto Recovery Lambda
resource "aws_lambda_function" "auto_recovery" {
  filename         = local.lambda_package_path
  function_name    = "${var.project_name}-auto-recovery"
  role            = aws_iam_role.lambda_role.arn
  handler         = "auto_recovery.recovery_engine.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 900  # 15 minutes for recovery operations
  memory_size     = var.lambda_memory_size
  
  source_code_hash = filebase64sha256(local.lambda_package_path)

  environment {
    variables = {
      RECOVERY_EVENTS_TABLE      = aws_dynamodb_table.recovery_events.name
      PREDICTION_EVENTS_TABLE    = aws_dynamodb_table.prediction_events.name
      INSTANCE_CONFIG_TABLE      = aws_dynamodb_table.instance_config.name
      RECOVERY_TIMEOUT_SECONDS   = "600"
      HEALTH_CHECK_RETRY_COUNT   = "3"
      HEALTH_CHECK_RETRY_DELAY   = "30"
      NOTIFICATION_ENABLED       = var.enable_notifications
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-auto-recovery"
  })
}

# Notifier Lambda
resource "aws_lambda_function" "notifier" {
  filename         = local.lambda_package_path
  function_name    = "${var.project_name}-notifier"
  role            = aws_iam_role.lambda_role.arn
  handler         = "notifier.notification_handler.lambda_handler"
  runtime         = var.lambda_runtime
  timeout         = 60
  memory_size     = 256
  
  source_code_hash = filebase64sha256(local.lambda_package_path)

  environment {
    variables = {
      RECOVERY_EVENTS_TABLE      = aws_dynamodb_table.recovery_events.name
      INSTANCE_CONFIG_TABLE      = aws_dynamodb_table.instance_config.name
      SNS_TOPIC_ARN              = var.enable_sns ? aws_sns_topic.notifications[0].arn : ""
      SLACK_WEBHOOK_URL          = var.slack_webhook_url
      SLACK_CHANNEL              = var.slack_channel
      SLACK_USERNAME             = var.slack_username
      TEAMS_WEBHOOK_URL          = var.teams_webhook_url
      NOTIFICATION_ENABLED       = var.enable_notifications
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-notifier"
  })
}

# Lambda layers for dependencies (if needed)
# Note: In production, you'd package dependencies separately
# For now, we assume boto3 is available in Lambda runtime

