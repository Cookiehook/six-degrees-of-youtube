resource "aws_alb" "six-degrees-of-youtube" {
  name                       = "six-degrees-of-youtube"
  drop_invalid_header_fields = "false"
  enable_deletion_protection = "false"
  enable_http2               = "true"
  idle_timeout               = "600"
  internal                   = "false"
  ip_address_type            = "ipv4"
  load_balancer_type         = "application"

  security_groups = [
    aws_security_group.six-degrees-of-youtube.id
  ]
  subnets = [
    aws_subnet.eu-west-2a-public.id,
    aws_subnet.eu-west-2b-public.id,
  ]

  tags = {
    service = "six-degrees-of-youtube"
  }
}

resource "aws_lb_listener" "six-degrees-of-youtube" {
  certificate_arn = data.aws_acm_certificate.cookiehook.arn

  default_action {
    target_group_arn = aws_lb_target_group.six-degrees-of-youtube.arn
    type             = "forward"
  }

  load_balancer_arn = aws_alb.six-degrees-of-youtube.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
}

resource "aws_lb_listener_rule" "six-degrees-of-youtube" {
  listener_arn = aws_lb_listener.six-degrees-of-youtube.arn
  priority     = "50000"

  action {
    target_group_arn = aws_lb_target_group.six-degrees-of-youtube.arn
    type             = "forward"
  }

  condition {
    path_pattern {
      values = ["*"]
    }
  }
}

resource "aws_lb_target_group" "six-degrees-of-youtube" {
  name = "six-degrees-of-youtube"
  port = 5000
  protocol = "HTTP"
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  health_check {
    path = "/health"
    protocol = "HTTP"
    interval = "20"
    timeout = "5"
    healthy_threshold = "5"
    unhealthy_threshold = "2"
  }
}
