resource "aws_iam_role" "six-degrees-of-youtube-ec2" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Allows EC2 instances to call AWS services on your behalf."
  managed_policy_arns  = [
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
    "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  ]
  max_session_duration = "3600"
  name                 = "six-degrees-of-youtube-ec2"
  path                 = "/"

  tags = {
    service = "six-degrees-of-youtube"
  }
}

resource "aws_iam_instance_profile" "six-degrees-of-youtube-ec2" {
  name = aws_iam_role.six-degrees-of-youtube-ec2.name
  path = "/"
  role = aws_iam_role.six-degrees-of-youtube-ec2.name
}


resource "aws_iam_role_policy_attachment" "CloudWatchLogsFullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
  role       = aws_iam_role.six-degrees-of-youtube-ec2.name
}

resource "aws_iam_role_policy_attachment" "SecretsManagerReadWrite" {
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
  role       = aws_iam_role.six-degrees-of-youtube-ec2.name
}
