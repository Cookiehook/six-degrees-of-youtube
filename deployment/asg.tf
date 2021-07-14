resource "aws_autoscaling_group" "six-degrees-of-youtube" {
  name = aws_launch_configuration.six-degrees-of-youtube.name
  min_size = "1"
  max_size = "5"
  desired_capacity = "1"
  wait_for_capacity_timeout = "10m"
  launch_configuration = aws_launch_configuration.six-degrees-of-youtube.name
  vpc_zone_identifier = [
    aws_subnet.eu-west-2a-private.id,
    aws_subnet.eu-west-2b-private.id,
  ]
  target_group_arns = [
    aws_lb_target_group.six-degrees-of-youtube.arn
  ]

  lifecycle {
    create_before_destroy = true
  }

}

resource "aws_launch_configuration" "six-degrees-of-youtube" {
  name = "six-degrees-of-youtube-${replace(timestamp(), ":", "")}"
  instance_type = "t2.medium"
  image_id = data.aws_ami.amazon-linux.id
  iam_instance_profile = aws_iam_instance_profile.six-degrees-of-youtube-ec2.arn
  user_data = data.template_file.six-degrees-of-youtube.rendered
  security_groups = [aws_security_group.six-degrees-of-youtube.id]
}

data "aws_ami" "amazon-linux" {
  most_recent = true
  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "template_file" "six-degrees-of-youtube" {
  template = file("${path.module}/templates/userdata.sh")
  vars = {
    aws_region = "eu-west-2"
    docker_tag = var.branch
  }
}