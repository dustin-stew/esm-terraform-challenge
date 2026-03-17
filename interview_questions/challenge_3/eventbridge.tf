# ------------------------------------------------------------------------------
# EventBridge Rule - Hourly Schedule
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "pipeline_schedule" {
  name                = "pipeline-schedule"
  description         = "Triggers data processing pipeline every 5 minutes"
  schedule_expression = "rate(5 minutes)"
}

# ------------------------------------------------------------------------------
# EventBridge Target - Step Functions
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_event_target" "step_functions" {
  rule      = aws_cloudwatch_event_rule.pipeline_schedule.name
  target_id = "data-pipeline"
  arn       = aws_sfn_state_machine.data_pipeline.arn
  role_arn  = aws_iam_role.eventbridge.arn
}

# ------------------------------------------------------------------------------
# EventBridge IAM Role - Allow triggering Step Functions
# ------------------------------------------------------------------------------

data "aws_iam_policy_document" "eventbridge_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "eventbridge" {
  name               = "pipeline-eventbridge-role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_role.json
}

data "aws_iam_policy_document" "eventbridge_permissions" {
  statement {
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.data_pipeline.arn]
  }
}

resource "aws_iam_role_policy" "eventbridge_permissions" {
  name   = "eventbridge-step-functions"
  role   = aws_iam_role.eventbridge.id
  policy = data.aws_iam_policy_document.eventbridge_permissions.json
}