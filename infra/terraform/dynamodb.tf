resource "aws_dynamodb_table" "recovery_events" {
  name           = "${var.project_name}-recovery-events"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "instance_id"
  range_key      = "timestamp"

  attribute {
    name = "instance_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-recovery-events"
  })
}

resource "aws_dynamodb_table" "prediction_events" {
  name           = "${var.project_name}-prediction-events"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "instance_id"
  range_key      = "timestamp"

  attribute {
    name = "instance_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-prediction-events"
  })
}

resource "aws_dynamodb_table" "instance_config" {
  name         = "${var.project_name}-instance-config"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "instance_id"

  attribute {
    name = "instance_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-instance-config"
  })
}

