# ------------------------------------------------------------------------------
# Step Functions IAM Role
# ------------------------------------------------------------------------------

data "aws_iam_policy_document" "sfn_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "step_functions" {
  name               = "pipeline-step-functions-role"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume_role.json
}

data "aws_iam_policy_document" "sfn_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.drain_queue.arn,
      aws_lambda_function.process_file.arn,
      aws_lambda_function.notify.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:GetLogDelivery",
      "logs:UpdateLogDelivery",
      "logs:DeleteLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutResourcePolicy",
      "logs:DescribeResourcePolicies",
      "logs:DescribeLogGroups"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "sfn_permissions" {
  name   = "step-functions-permissions"
  role   = aws_iam_role.step_functions.id
  policy = data.aws_iam_policy_document.sfn_permissions.json
}

# ------------------------------------------------------------------------------
# Step Functions State Machine
# ------------------------------------------------------------------------------

resource "aws_sfn_state_machine" "data_pipeline" {
  name     = "sports-data-pipeline"
  role_arn = aws_iam_role.step_functions.arn

  definition = jsonencode({
    Comment = "Sports data processing pipeline — drains SQS, fans out per file"
    StartAt = "DrainQueue"

    States = {
      DrainQueue = {
        Type     = "Task"
        Resource = aws_lambda_function.drain_queue.arn
        Next     = "CheckMessagesExist"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "NotifyFailure"
          ResultPath  = "$.error"
        }]
      }

      CheckMessagesExist = {
        Type = "Choice"
        Choices = [{
          Variable      = "$.messageCount"
          NumericEquals = 0
          Next          = "NoFilesToProcess"
        }]
        Default = "ProcessFiles"
      }

      NoFilesToProcess = {
        Type = "Pass"
        Result = {
          status  = "skipped"
          message = "No messages in queue"
        }
        End = true
      }

      ProcessFiles = {
        Type      = "Map"
        ItemsPath = "$.files"
        MaxConcurrency = 10

        Iterator = {
          StartAt = "ProcessSingleFile"
          States = {
            ProcessSingleFile = {
              Type     = "Task"
              Resource = aws_lambda_function.process_file.arn
              Retry = [{
                ErrorEquals     = ["States.TaskFailed"]
                IntervalSeconds = 5
                MaxAttempts     = 3
                BackoffRate     = 2.0
              }]
              End = true
            }
          }
        }

        ResultPath = "$.processResults"
        Next       = "NotifySuccess"

        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "NotifyFailure"
          ResultPath  = "$.error"
        }]
      }

      NotifySuccess = {
        Type     = "Task"
        Resource = aws_lambda_function.notify.arn
        End      = true
      }

      NotifyFailure = {
        Type     = "Task"
        Resource = aws_lambda_function.notify.arn
        End      = true
      }
    }
  })
}