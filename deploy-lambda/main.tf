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

data "aws_acm_certificate" "cookiehook" {
  domain = "*.cookiehook.com"
}

data "aws_route53_zone" "cookiehook" {
  name = "cookiehook.com"
}

data "aws_iam_role" "rds-monitoring" {
  name = "rds-monitoring-role"
}
