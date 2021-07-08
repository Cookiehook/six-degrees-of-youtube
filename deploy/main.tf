terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "eu-west-2"
}

resource "aws_lambda_function" "six-degrees-of-youtube" {
  function_name = "six-degrees-of-youtube"
  s3_bucket = var.artifact_bucket
  s3_key = var.artifact_name
  role = var.iam_role
  handler = "src.app.entrypoint"
  runtime = "python3.8"
}

resource "aws_lambda_permission" "apigw" {
  statement_id = "AllowAPIGatewayInvoke"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.six-degrees-of-youtube.function_name
  principal = "apigateway.amazonaws.com"
  # The "/*/*" portion grants access from any method on any resource within the API Gateway REST API.
  source_arn = "${aws_api_gateway_rest_api.six-degrees-of-youtube.execution_arn}/*/*"
}

output "base_url" {
  value = aws_api_gateway_deployment.six-degrees-of-youtube.invoke_url
}
