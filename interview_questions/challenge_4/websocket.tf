# ------------------------------------------------------------------------------
# DynamoDB - WebSocket Connections
# ------------------------------------------------------------------------------

resource "aws_dynamodb_table" "ws_connections" {
  name         = "nfl-ws-connections"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "connectionId"

  attribute {
    name = "connectionId"
    type = "S"
  }
}

# ------------------------------------------------------------------------------
# WebSocket API Gateway
# ------------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "scoreboard_ws" {
  name                       = "nfl-scoreboard-ws"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

resource "aws_apigatewayv2_stage" "ws_prod" {
  api_id      = aws_apigatewayv2_api.scoreboard_ws.id
  name        = "prod"
  auto_deploy = true
}

# ------------------------------------------------------------------------------
# WebSocket IAM Role (shared by ws_ Lambdas)
# ------------------------------------------------------------------------------

data "aws_iam_policy_document" "ws_lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ws_lambda" {
  name               = "nfl-ws-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.ws_lambda_assume_role.json
}

data "aws_iam_policy_document" "ws_lambda_permissions" {
  # Connections table access
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
      "dynamodb:Scan",
      "dynamodb:GetItem"
    ]
    resources = [aws_dynamodb_table.ws_connections.arn]
  }

  # Read streams from scores and standings tables
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetRecords",
      "dynamodb:GetShardIterator",
      "dynamodb:DescribeStream",
      "dynamodb:ListStreams"
    ]
    resources = [
      "${aws_dynamodb_table.scores.arn}/stream/*",
      "${aws_dynamodb_table.standings.arn}/stream/*"
    ]
  }

  # Post to WebSocket connections
  statement {
    effect    = "Allow"
    actions   = ["execute-api:ManageConnections"]
    resources = ["${aws_apigatewayv2_api.scoreboard_ws.execution_arn}/*"]
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

resource "aws_iam_role_policy" "ws_lambda_permissions" {
  name   = "ws-lambda-permissions"
  role   = aws_iam_role.ws_lambda.id
  policy = data.aws_iam_policy_document.ws_lambda_permissions.json
}

# ------------------------------------------------------------------------------
# Lambda: WebSocket Connect
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "ws_connect" {
  function_name    = "ws-connect"
  role             = aws_iam_role.ws_lambda.arn
  handler          = "handler.ws_connect"
  runtime          = "python3.11"
  timeout          = 10
  memory_size      = 128
  filename         = "${path.module}/../app/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../app/handler.zip")

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.ws_connections.name
    }
  }
}

# ------------------------------------------------------------------------------
# Lambda: WebSocket Disconnect
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "ws_disconnect" {
  function_name    = "ws-disconnect"
  role             = aws_iam_role.ws_lambda.arn
  handler          = "handler.ws_disconnect"
  runtime          = "python3.11"
  timeout          = 10
  memory_size      = 128
  filename         = "${path.module}/../app/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../app/handler.zip")

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.ws_connections.name
    }
  }
}

# ------------------------------------------------------------------------------
# Lambda: WebSocket Default (no-op)
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "ws_default" {
  function_name    = "ws-default"
  role             = aws_iam_role.ws_lambda.arn
  handler          = "handler.ws_default"
  runtime          = "python3.11"
  timeout          = 10
  memory_size      = 128
  filename         = "${path.module}/../app/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../app/handler.zip")
}

# ------------------------------------------------------------------------------
# Lambda: Broadcast DynamoDB Stream changes to WebSocket clients
# ------------------------------------------------------------------------------

resource "aws_lambda_function" "ws_broadcast" {
  function_name    = "ws-broadcast"
  role             = aws_iam_role.ws_lambda.arn
  handler          = "handler.ws_broadcast"
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 128
  filename         = "${path.module}/../app/handler.zip"
  source_code_hash = filebase64sha256("${path.module}/../app/handler.zip")

  environment {
    variables = {
      CONNECTIONS_TABLE = aws_dynamodb_table.ws_connections.name
      WS_ENDPOINT      = "https://${aws_apigatewayv2_api.scoreboard_ws.id}.execute-api.us-east-1.amazonaws.com/prod"
    }
  }
}

# ------------------------------------------------------------------------------
# DynamoDB Stream → Lambda Event Source Mappings
# ------------------------------------------------------------------------------

resource "aws_lambda_event_source_mapping" "scores_stream" {
  event_source_arn  = aws_dynamodb_table.scores.stream_arn
  function_name     = aws_lambda_function.ws_broadcast.arn
  starting_position = "LATEST"
  batch_size        = 10
}

resource "aws_lambda_event_source_mapping" "standings_stream" {
  event_source_arn  = aws_dynamodb_table.standings.stream_arn
  function_name     = aws_lambda_function.ws_broadcast.arn
  starting_position = "LATEST"
  batch_size        = 10
}

# ------------------------------------------------------------------------------
# WebSocket Routes & Integrations
# ------------------------------------------------------------------------------

resource "aws_apigatewayv2_integration" "ws_connect" {
  api_id             = aws_apigatewayv2_api.scoreboard_ws.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.ws_connect.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "ws_connect" {
  api_id    = aws_apigatewayv2_api.scoreboard_ws.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.ws_connect.id}"
}

resource "aws_apigatewayv2_integration" "ws_disconnect" {
  api_id             = aws_apigatewayv2_api.scoreboard_ws.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.ws_disconnect.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "ws_disconnect" {
  api_id    = aws_apigatewayv2_api.scoreboard_ws.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.ws_disconnect.id}"
}

resource "aws_apigatewayv2_integration" "ws_default" {
  api_id             = aws_apigatewayv2_api.scoreboard_ws.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.ws_default.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "ws_default" {
  api_id    = aws_apigatewayv2_api.scoreboard_ws.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.ws_default.id}"
}

# ------------------------------------------------------------------------------
# Lambda Permissions for API Gateway WebSocket
# ------------------------------------------------------------------------------

resource "aws_lambda_permission" "ws_connect" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_connect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.scoreboard_ws.execution_arn}/*/*"
}

resource "aws_lambda_permission" "ws_disconnect" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_disconnect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.scoreboard_ws.execution_arn}/*/*"
}

resource "aws_lambda_permission" "ws_default" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_default.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.scoreboard_ws.execution_arn}/*/*"
}

# ------------------------------------------------------------------------------
# CloudWatch Log Groups
# ------------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "ws_connect" {
  name              = "/aws/lambda/${aws_lambda_function.ws_connect.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ws_disconnect" {
  name              = "/aws/lambda/${aws_lambda_function.ws_disconnect.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ws_default" {
  name              = "/aws/lambda/${aws_lambda_function.ws_default.function_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "ws_broadcast" {
  name              = "/aws/lambda/${aws_lambda_function.ws_broadcast.function_name}"
  retention_in_days = 14
}