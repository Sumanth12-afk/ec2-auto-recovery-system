variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "ec2-auto-recovery"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "sns_topic_name" {
  description = "SNS topic name for notifications (leave empty to disable SNS)"
  type        = string
  default     = "ec2-auto-recovery-notifications"
}

variable "enable_sns" {
  description = "Enable SNS topic creation (set to false if only using webhooks)"
  type        = bool
  default     = true
}

variable "slack_webhook_url" {
  description = "Slack webhook URL (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "slack_channel" {
  description = "Slack channel to send notifications to (e.g., #team-collab)"
  type        = string
  default     = "#general"
}

variable "slack_username" {
  description = "Slack username for notifications"
  type        = string
  default     = "EC2 Auto-Recovery"
}

variable "teams_webhook_url" {
  description = "Microsoft Teams webhook URL (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "monitoring_schedule" {
  description = "CloudWatch Events schedule for predictive monitoring (cron expression)"
  type        = string
  default     = "rate(1 hour)"
}

variable "enable_notifications" {
  description = "Enable notifications"
  type        = bool
  default     = true
}

variable "prediction_lookback_hours" {
  description = "Hours to look back for predictive analysis"
  type        = number
  default     = 168  # 7 days
}

variable "high_confidence_threshold" {
  description = "High confidence threshold for predictions"
  type        = number
  default     = 0.8
}

variable "medium_confidence_threshold" {
  description = "Medium confidence threshold for predictions"
  type        = number
  default     = 0.6
}

