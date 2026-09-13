# API - The container that owns the public URL and TLS certificate. Using HTTP API rather than 
# REST API due to it being more cost effective.

resource "aws_apigatewayv2_api" "http" {
  name          = "parking-lot-api"
  protocol_type = "HTTP"

  tags = {
    Project = "parking-lot-api"
  }
}

# Integration - Connects the API and Mangum to handle requests

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

# Routing Rule - Catches everything and passes every path straight to Lambda so we don't have 
# to delcare various different routes

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# The Stage - a deployed instance of the API that carries a URL. $default giving a clean URL with no path 
# prefix and auto_deploy = true to route changes to go live immediately.

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

# Invoke - lets API Gateway invoke the function

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
