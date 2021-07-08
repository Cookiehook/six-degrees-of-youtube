resource "aws_api_gateway_rest_api" "six-degrees-of-youtube" {
  name = "six-degrees-of-youtube"
  description = "API Gateway for the six degrees of youtube project"
}

resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.six-degrees-of-youtube.id
  parent_id = aws_api_gateway_rest_api.six-degrees-of-youtube.root_resource_id
  path_part = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.six-degrees-of-youtube.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.six-degrees-of-youtube.id
  resource_id = aws_api_gateway_method.proxy.resource_id
  http_method = aws_api_gateway_method.proxy.http_method
  integration_http_method = "GET"
  type = "AWS_PROXY"
  uri = aws_lambda_function.six-degrees-of-youtube.invoke_arn
}

resource "aws_api_gateway_method" "proxy_root" {
  rest_api_id = aws_api_gateway_rest_api.six-degrees-of-youtube.id
  resource_id = aws_api_gateway_rest_api.six-degrees-of-youtube.root_resource_id
  http_method = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_root" {
  rest_api_id = aws_api_gateway_rest_api.six-degrees-of-youtube.id
  resource_id = aws_api_gateway_method.proxy_root.resource_id
  http_method = aws_api_gateway_method.proxy_root.http_method
  integration_http_method = "GET"
  type = "AWS_PROXY"
  uri = aws_lambda_function.six-degrees-of-youtube.invoke_arn
}

resource "aws_api_gateway_deployment" "six-degrees-of-youtube" {
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.lambda_root,]
  rest_api_id = aws_api_gateway_rest_api.six-degrees-of-youtube.id
  stage_name = "test"
}