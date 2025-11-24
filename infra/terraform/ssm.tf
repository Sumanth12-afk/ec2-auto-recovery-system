# SSM Documents for recovery operations
resource "aws_ssm_document" "restart_services" {
  name            = "${var.project_name}-restart-services"
  document_type   = "Command"
  document_format = "YAML"

  content = file("${path.module}/../../src/ssm/restart_services.yml")

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-restart-services"
  })
}

resource "aws_ssm_document" "verify_health" {
  name            = "${var.project_name}-verify-health"
  document_type   = "Command"
  document_format = "YAML"

  content = file("${path.module}/../../src/ssm/verify_health.yml")

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-verify-health"
  })
}

resource "aws_ssm_document" "diagnostics" {
  name            = "${var.project_name}-diagnostics"
  document_type   = "Command"
  document_format = "YAML"

  content = file("${path.module}/../../src/ssm/diagnostics.yml")

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-diagnostics"
  })
}

