# ------------------------------------------------------------------------------
# API Gateway - REST API
# ------------------------------------------------------------------------------

resource "aws_api_gateway_rest_api" "scoreboard" {
  name        = "nfl-scoreboard-api"
  description = "NFL Scoreboard API"
}

# ------------------------------------------------------------------------------
# /scores resource
# ------------------------------------------------------------------------------

resource "aws_api_gateway_resource" "scores" {
  rest_api_id = aws_api_gateway_rest_api.scoreboard.id
  parent_id   = aws_api_gateway_rest_api.scoreboard.root_resource_id
  path_part   = "scores"
}

resource "aws_api_gateway_method" "get_scores" {
  rest_api_id   = aws_api_gateway_rest_api.scoreboard.id
  resource_id   = aws_api_gateway_resource.scores.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_scores" {
  rest_api_id             = aws_api_gateway_rest_api.scoreboard.id
  resource_id             = aws_api_gateway_resource.scores.id
  http_method             = aws_api_gateway_method.get_scores.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_scores.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_scores" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_scores.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.scoreboard.execution_arn}/*/*"
}

# ------------------------------------------------------------------------------
# /standings resource
# ------------------------------------------------------------------------------

resource "aws_api_gateway_resource" "standings" {
  rest_api_id = aws_api_gateway_rest_api.scoreboard.id
  parent_id   = aws_api_gateway_rest_api.scoreboard.root_resource_id
  path_part   = "standings"
}

resource "aws_api_gateway_method" "get_standings" {
  rest_api_id   = aws_api_gateway_rest_api.scoreboard.id
  resource_id   = aws_api_gateway_resource.standings.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_standings" {
  rest_api_id             = aws_api_gateway_rest_api.scoreboard.id
  resource_id             = aws_api_gateway_resource.standings.id
  http_method             = aws_api_gateway_method.get_standings.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_standings.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_standings" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_standings.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.scoreboard.execution_arn}/*/*"
}

# ------------------------------------------------------------------------------
# Deployment & Stage
# ------------------------------------------------------------------------------

resource "aws_api_gateway_deployment" "scoreboard" {
  rest_api_id = aws_api_gateway_rest_api.scoreboard.id

  depends_on = [
    aws_api_gateway_integration.get_scores,
    aws_api_gateway_integration.get_standings
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  rest_api_id   = aws_api_gateway_rest_api.scoreboard.id
  deployment_id = aws_api_gateway_deployment.scoreboard.id
  stage_name    = "prod"
}