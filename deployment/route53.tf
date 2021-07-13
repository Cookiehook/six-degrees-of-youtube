resource "aws_route53_record" "api" {
  name    = "six-degrees-of-youtube.cookiehook.com"
  records = [aws_alb.six-degrees-of-youtube.dns_name]
  ttl     = "300"
  type    = "CNAME"
  zone_id = data.aws_route53_zone.cookiehook.zone_id
}
