resource "aws_alb" "six-degrees-of-youtube" {
  name                       = "six-degrees-of-youtube"
  drop_invalid_header_fields = "false"
  enable_deletion_protection = "false"
  enable_http2               = "true"
  idle_timeout               = "60"
  internal                   = "false"
  ip_address_type            = "ipv4"
  load_balancer_type         = "application"

  security_groups = [
    aws_security_group.web-rds.id
  ]
  subnets = [
    aws_subnet.eu-west-2a-public.id,
    aws_subnet.eu-west-2a-public.id,
    aws_subnet.eu-west-2b-public.id,
    aws_subnet.eu-west-2b-public.id,
    aws_subnet.eu-west-2c-public.id,
    aws_subnet.eu-west-2c-public.id,
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
  action {
    target_group_arn = aws_lb_target_group.six-degrees-of-youtube.arn
    type             = "forward"
  }

  condition {
    path_pattern {
      values = ["/lambda/six-degrees-of-youtube"]
    }
  }

  listener_arn = aws_lb_listener.six-degrees-of-youtube.arn
  priority     = "50000"
}

resource "aws_lb_listener_certificate" "six-degrees-of-youtube" {
  listener_arn    = aws_lb_listener.six-degrees-of-youtube.arn
  certificate_arn = data.aws_acm_certificate.cookiehook.arn
}

resource "aws_lb_target_group" "six-degrees-of-youtube" {
  health_check {
    enabled             = "false"
    healthy_threshold   = "5"
    interval            = "35"
    matcher             = "200"
    path                = "/"
    timeout             = "30"
    unhealthy_threshold = "2"
  }

  lambda_multi_value_headers_enabled = "false"
  name                               = "six-degrees-of-youtube"
  target_type                        = "lambda"
}

resource "aws_lb_target_group_attachment" "six-degrees-of-youtube" {
  depends_on       = [ aws_lambda_permission.alb ]
  target_group_arn = aws_lb_target_group.six-degrees-of-youtube.arn
  target_id        = aws_lambda_alias.live.arn
}
