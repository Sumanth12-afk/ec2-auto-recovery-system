# SNS Topic for notifications (optional)
resource "aws_sns_topic" "notifications" {
  count = var.enable_sns ? 1 : 0
  name  = var.sns_topic_name

  tags = merge(local.common_tags, {
    Name = var.sns_topic_name
  })
}

# SNS Topic Subscription (optional - configure as needed)
# Uncomment and configure if you want email subscriptions
# resource "aws_sns_topic_subscription" "email" {
#   topic_arn = aws_sns_topic.notifications.arn
#   protocol  = "email"
#   endpoint  = "your-email@example.com"
# }

