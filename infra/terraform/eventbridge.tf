# EventBridge rule for scheduled predictive monitoring
resource "aws_cloudwatch_event_rule" "predictive_schedule" {
  name                = "${var.project_name}-predictive-schedule"
  description         = "Schedule for predictive monitoring"
  schedule_expression = var.monitoring_schedule

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-predictive-schedule"
  })
}

resource "aws_cloudwatch_event_target" "predictive_monitor_target" {
  rule      = aws_cloudwatch_event_rule.predictive_schedule.name
  target_id = "PredictiveMonitorTarget"
  arn       = aws_lambda_function.predictive_monitor.arn
}

resource "aws_lambda_permission" "predictive_monitor_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.predictive_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.predictive_schedule.arn
}

# EventBridge rule for EC2 status changes
resource "aws_cloudwatch_event_rule" "ec2_status_changes" {
  name        = "${var.project_name}-ec2-status-changes"
  description = "Capture EC2 instance status check failures"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = [
      "EC2 Instance State-change Notification",
      "EC2 Instance Status-change Notification"
    ]
    detail = {
      state = ["stopped", "stopping", "stopped"]
    }
  })

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-ec2-status-changes"
  })
}

resource "aws_cloudwatch_event_target" "health_monitor_target" {
  rule      = aws_cloudwatch_event_rule.ec2_status_changes.name
  target_id = "HealthMonitorTarget"
  arn       = aws_lambda_function.health_monitor.arn
}

resource "aws_lambda_permission" "health_monitor_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_status_changes.arn
}

# EventBridge rule to trigger recovery on high-confidence predictions
resource "aws_cloudwatch_event_rule" "trigger_recovery" {
  name        = "${var.project_name}-trigger-recovery"
  description = "Trigger recovery for high-confidence predictions"

  event_pattern = jsonencode({
    source      = ["aws.dynamodb"]
    detail-type = ["DynamoDB Stream Record"]
    detail = {
      eventName = ["INSERT", "MODIFY"]
      dynamodb = {
        StreamViewType = ["NEW_AND_OLD_IMAGES"]
        NewImage = {
          confidence = {
            S = ["high"]
          }
        }
      }
    }
  })

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-trigger-recovery"
  })
}

# Alternative: Use EventBridge to trigger recovery from predictive monitor
resource "aws_cloudwatch_event_rule" "predictive_recovery_trigger" {
  name        = "${var.project_name}-predictive-recovery-trigger"
  description = "Trigger recovery from predictive monitor output"

  event_pattern = jsonencode({
    source      = ["${var.project_name}-predictive-monitor"]
    detail-type = ["High Confidence Prediction"]
  })

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-predictive-recovery-trigger"
  })
}

resource "aws_cloudwatch_event_target" "auto_recovery_target" {
  rule      = aws_cloudwatch_event_rule.predictive_recovery_trigger.name
  target_id = "AutoRecoveryTarget"
  arn       = aws_lambda_function.auto_recovery.arn
}

resource "aws_lambda_permission" "auto_recovery_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auto_recovery.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.predictive_recovery_trigger.arn
}

# EventBridge rule to trigger notifications after recovery
resource "aws_cloudwatch_event_rule" "recovery_notification" {
  name        = "${var.project_name}-recovery-notification"
  description = "Trigger notifications after recovery events"

  event_pattern = jsonencode({
    source      = ["${var.project_name}-auto-recovery"]
    detail-type = ["Recovery Completed"]
  })

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-recovery-notification"
  })
}

resource "aws_cloudwatch_event_target" "notifier_target" {
  rule      = aws_cloudwatch_event_rule.recovery_notification.name
  target_id = "NotifierTarget"
  arn       = aws_lambda_function.notifier.arn
}

resource "aws_lambda_permission" "notifier_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.recovery_notification.arn
}

