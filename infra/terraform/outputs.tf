output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    recovery_events   = aws_dynamodb_table.recovery_events.name
    prediction_events = aws_dynamodb_table.prediction_events.name
    instance_config   = aws_dynamodb_table.instance_config.name
  }
}

output "lambda_functions" {
  description = "Lambda function ARNs"
  value = {
    predictive_monitor = aws_lambda_function.predictive_monitor.arn
    health_monitor     = aws_lambda_function.health_monitor.arn
    auto_recovery      = aws_lambda_function.auto_recovery.arn
    notifier           = aws_lambda_function.notifier.arn
  }
}

output "sns_topic_arn" {
  description = "SNS topic ARN for notifications"
  value       = var.enable_sns ? aws_sns_topic.notifications[0].arn : null
}

output "eventbridge_rules" {
  description = "EventBridge rule ARNs"
  value = {
    predictive_schedule = aws_cloudwatch_event_rule.predictive_schedule.arn
    ec2_status_changes  = aws_cloudwatch_event_rule.ec2_status_changes.arn
  }
}

output "iam_role_arn" {
  description = "IAM role ARN for Lambda functions"
  value       = aws_iam_role.lambda_role.arn
}

