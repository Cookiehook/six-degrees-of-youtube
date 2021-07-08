resource "aws_lambda_function" "six-degrees-of-youtube" {
  function_name = "six-degrees-of-youtube"
  s3_bucket = var.artifact_bucket
  s3_key = var.artifact_name
  role = data.aws_iam_role.lambda.arn
  handler = "src.app.entrypoint"
  runtime = "python3.8"
}

// Alias and permissions derived from:
// https://floqast.com/engineering-blog/post/attaching-lambdas-to-an-existing-alb-with-terraform/
resource aws_lambda_alias "live" {
  name = "live"
  description = "Live alias"
  function_name = aws_lambda_function.six-degrees-of-youtube.arn
  function_version = aws_lambda_function.six-degrees-of-youtube.version
}

resource aws_lambda_permission "alb" {
  statement_id = "AllowExecutionFromALB"
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.six-degrees-of-youtube.function_name
  principal = "elasticloadbalancing.amazonaws.com"
  qualifier = aws_lambda_alias.live.name
  source_arn = aws_lb_target_group.six-degrees-of-youtube.arn
}
