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

data "aws_security_group" "default" {
  name = "default"
}

data "aws_subnet" "eu-west-2a" {
  filter {
    name = "tag:Name"
    values = ["default-eu-west-2a"]
  }
}

data "aws_subnet" "eu-west-2b" {
  filter {
    name = "tag:Name"
    values = ["default-eu-west-2b"]
  }
}

data "aws_subnet" "eu-west-2c" {
  filter {
    name = "tag:Name"
    values = ["default-eu-west-2c"]
  }
}

data "aws_acm_certificate" "cookiehook" {
  domain = "*.cookiehook.com"
}

data "aws_iam_role" "lambda" {
  name = "six-degrees-of-youtube-lambda"
}

data "aws_route53_zone" "cookiehook" {
  name = "cookiehook.com"
}
