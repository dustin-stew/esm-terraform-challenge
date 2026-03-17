# ------------------------------------------------------------------------------
# Lambda IAM Role (shared by all functions)
# ------------------------------------------------------------------------------

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda" {
  name               = "pipeline-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_permissions" {
  # S3 access
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
      "s3:DeleteObject"
    ]
    resources = [
      aws_s3_bucket.data_pipeline.arn,
      "${aws_s3_bucket.data_pipeline.arn}/*"
    ]
  }

  # SQS access
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = [aws_sqs_queue.file_events.arn]
  }

  # SNS publish
  statement {
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.pipeline_notifications.arn]
  }

  # CloudWatch Logs
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }
}

resource "aws_iam_role_policy" "lambda_permissions" {
  name   = "lambda-permissions"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

# ------------------------------------------------------------------------------
# Lambda: Drain Queue
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "drain_queue" {
  function_name = "drain-queue"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.drain_queue"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 128

  filename = "${path.module}/../app/handler.zip"

  environment {
    variables = {
      QUEUE_URL = aws_sqs_queue.file_events.id
    }
  }
}

# ------------------------------------------------------------------------------
# Lambda: Process File
# Swap this to Fargate for lower cost, more flexible compute
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "process_file" {
  function_name = "process-file"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.process_file"
  runtime       = "python3.11"
  timeout       = 900  # 15 min max — if exceeded, switch to Fargate
  memory_size   = 512

  filename = "${path.module}/../app/handler.zip"

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.data_pipeline.id
      DEST_PREFIX = "processed/"
    }
  }
}

# ------------------------------------------------------------------------------
# Lambda: Notify
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "notify" {
  function_name = "notify"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.notify"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 128

  filename = "${path.module}/../app/handler.zip"

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.pipeline_notifications.arn
    }
  }
}

# ------------------------------------------------------------------------------
# CloudWatch Log Groups
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "drain_queue" {
  name              = "/aws/lambda/${aws_lambda_function.drain_queue.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "process_file" {
  name              = "/aws/lambda/${aws_lambda_function.process_file.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "notify" {
  name              = "/aws/lambda/${aws_lambda_function.notify.function_name}"
  retention_in_days = 14
}