# ------------------------------------------------------------------------------
# Lambda IAM Role
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

resource "aws_iam_role" "api_lambda" {
  name               = "nfl-api-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "lambda_permissions" {
  # DynamoDB read access
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [
      aws_dynamodb_table.scores.arn,
      aws_dynamodb_table.standings.arn
    ]
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
  role   = aws_iam_role.api_lambda.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

# ------------------------------------------------------------------------------
# Lambda: Get Scores
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "get_scores" {
  function_name = "get-scores"
  role          = aws_iam_role.api_lambda.arn
  handler       = "handler.get_scores"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 128

  filename         = "${path.module}/../app/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../app/handler.zip")

  environment {
    variables = {
      SCORES_TABLE = aws_dynamodb_table.scores.name
    }
  }
}

# ------------------------------------------------------------------------------
# Lambda: Get Standings
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "get_standings" {
  function_name = "get-standings"
  role          = aws_iam_role.api_lambda.arn
  handler       = "handler.get_standings"
  runtime       = "python3.11"
  timeout       = 10
  memory_size   = 128

  filename         = "${path.module}/../app/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../app/handler.zip")

  environment {
    variables = {
      STANDINGS_TABLE = aws_dynamodb_table.standings.name
    }
  }
}

# ------------------------------------------------------------------------------
# CloudWatch Log Groups
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "get_scores" {
  name              = "/aws/lambda/${aws_lambda_function.get_scores.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "get_standings" {
  name              = "/aws/lambda/${aws_lambda_function.get_standings.function_name}"
  retention_in_days = 14
}