# ------------------------------------------------------------------------------
# SNS Topic - Pipeline Notifications for Analysts
# ------------------------------------------------------------------------------

resource "aws_sns_topic" "pipeline_notifications" {
  name = "pipeline-notifications"
}