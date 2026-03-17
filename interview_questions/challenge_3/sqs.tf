# ------------------------------------------------------------------------------
# SQS Queue - Buffer for S3 file arrival events
# ------------------------------------------------------------------------------

resource "aws_sqs_queue" "file_events" {
  name                       = "sports-data-file-events"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
}

resource "aws_sqs_queue_policy" "allow_s3" {
  queue_url = aws_sqs_queue.file_events.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.file_events.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_s3_bucket.data_pipeline.arn
        }
      }
    }]
  })
}

# ------------------------------------------------------------------------------
# S3 → SQS Notification
# ------------------------------------------------------------------------------

resource "aws_s3_bucket_notification" "file_arrival" {
  bucket = aws_s3_bucket.data_pipeline.id

  queue {
    queue_arn     = aws_sqs_queue.file_events.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "raw/"
  }

  depends_on = [aws_sqs_queue_policy.allow_s3]
}