resource "null_resource" "prepare_archive" {
  provisioner "local-exec" {
    command = "cd .. && pipenv run python deploy/scripts/prepare_archive.py"
  }
}

data "archive_file" "lambda_zip" {
  depends_on = [null_resource.prepare_archive]
  type = "zip"
  source_dir = "../build"
  output_path = "../build/lambda.zip"
}

resource "aws_lambda_function" "six-degrees-of-youtube" {
  function_name    = "six-degrees-of-youtube"
  filename         = "../build/lambda.zip"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role             = aws_iam_role.lambda.arn
  handler          = "src.app.entrypoint"
  runtime          = "python3.8"
  timeout          = 900
  vpc_config {
    security_group_ids = [aws_security_group.six-degrees-of-youtube.id]
    subnet_ids = [
      aws_subnet.eu-west-2a-public.id,
      aws_subnet.eu-west-2a-private.id,
      aws_subnet.eu-west-2b-public.id,
      aws_subnet.eu-west-2b-private.id,
    ]
  }
  environment {
    variables = {
      "PYTHONUNBUFFERED": 1
    }
  }
}

// Alias and permissions derived from:
// https://floqast.com/engineering-blog/post/attaching-lambdas-to-an-existing-alb-with-terraform/
resource aws_lambda_alias "live" {
  name             = "live"
  description      = "Live alias"
  function_name    = aws_lambda_function.six-degrees-of-youtube.arn
  function_version = aws_lambda_function.six-degrees-of-youtube.version
}

resource aws_lambda_permission "alb" {
  statement_id  = "AllowExecutionFromALB"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.six-degrees-of-youtube.function_name
  principal     = "elasticloadbalancing.amazonaws.com"
  qualifier     = aws_lambda_alias.live.name
  source_arn    = aws_lb_target_group.six-degrees-of-youtube.arn
}
