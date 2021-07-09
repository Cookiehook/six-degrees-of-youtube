resource "aws_vpc" "six-degrees-of-youtube" {
  assign_generated_ipv6_cidr_block = "false"
  cidr_block                       = "172.30.0.0/16"
  enable_dns_hostnames             = "true"
  enable_dns_support               = "true"
  instance_tenancy                 = "default"

  tags = {
    Name    = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_security_group" "web-rds" {

  egress {
    cidr_blocks      = ["0.0.0.0/0"]
    from_port        = "0"
    ipv6_cidr_blocks = ["::/0"]
    protocol         = "tcp"
    self             = "false"
    to_port          = "65535"
  }

  egress {
    from_port = "5432"
    protocol  = "tcp"
    self      = "true"
    to_port   = "5432"
  }

  ingress {
    cidr_blocks      = ["0.0.0.0/0"]
    from_port        = "0"
    ipv6_cidr_blocks = ["::/0"]
    protocol         = "tcp"
    self             = "false"
    to_port          = "65535"
  }

  ingress {
    from_port = "5432"
    protocol  = "tcp"
    self      = "true"
    to_port   = "5432"
  }

  name   = "web-rds"
  vpc_id = aws_vpc.six-degrees-of-youtube.id
  tags = {
    Name    = "web-rds"
    service = "six-degrees-of-youtube"
  }
}

// Subnets
resource "aws_subnet" "eu-west-2a-public" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  assign_ipv6_address_on_creation = "false"
  cidr_block                      = "172.30.1.0/24"
  map_public_ip_on_launch         = "false"

  tags = {
    Name = "six-degrees-of-youtube-eu-west-2a-public"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2a-private" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  assign_ipv6_address_on_creation = "false"
  cidr_block                      = "172.30.2.0/24"
  map_public_ip_on_launch         = "false"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a-private"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2b-public" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  assign_ipv6_address_on_creation = "false"
  cidr_block                      = "172.30.3.0/24"
  map_public_ip_on_launch         = "false"

  tags = {
    Name = "six-degrees-of-youtube-eu-west-2b-public"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2b-private" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  assign_ipv6_address_on_creation = "false"
  cidr_block                      = "172.30.4.0/24"
  map_public_ip_on_launch         = "false"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a-private"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2c-public" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  assign_ipv6_address_on_creation = "false"
  cidr_block                      = "172.30.5.0/24"
  map_public_ip_on_launch         = "false"

  tags = {
    Name = "six-degrees-of-youtube-eu-west-2c-public"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2c-private" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  assign_ipv6_address_on_creation = "false"
  cidr_block                      = "172.30.6.0/24"
  map_public_ip_on_launch         = "false"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2c-private"
    service = "six-degrees-of-youtube"
  }
}
// NOTE - These elastic IP allocations are not created by terraform.
// These are manually created once, and referenced here
resource "aws_nat_gateway" "six-degrees-of-youtube-eu-west-2a" {
  allocation_id     = "eipalloc-0ba46ac6d13aa16e3"
  connectivity_type = "public"
  subnet_id         = aws_subnet.eu-west-2a-public.id

  tags = {
    Name    = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_nat_gateway" "six-degrees-of-youtube-eu-west-2b" {
  allocation_id     = "eipalloc-091d06920346b94c6"
  connectivity_type = "public"
  subnet_id         = aws_subnet.eu-west-2b-public.id

  tags = {
    Name    = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_nat_gateway" "six-degrees-of-youtube-eu-west-2c" {
  allocation_id     = "eipalloc-06e0cd81870d85ceb"
  connectivity_type = "public"
  subnet_id         = aws_subnet.eu-west-2c-public.id

  tags = {
    Name    = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_internet_gateway" "apigw" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id
  tags = {
    Name    = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

// Route Tables
resource "aws_route_table" "default" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.apigw.id
  }

  tags = {
    Name    = "six-degrees-of-youtube-public"
    service = "six-degrees-of-youtube"
  }

}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.six-degrees-of-youtube-eu-west-2a.id
  }

  tags = {
    Name    = "six-degrees-of-youtube-private"
    service = "six-degrees-of-youtube"
  }

}

// Route Table associations with subnets / VPC
resource "aws_main_route_table_association" "default" {
  route_table_id = aws_route_table.default.id
  vpc_id         = aws_vpc.six-degrees-of-youtube.id
}

resource "aws_route_table_association" "public-2a" {
  route_table_id = aws_route_table.public.id
  subnet_id      = aws_subnet.eu-west-2a-public.id
}

resource "aws_route_table_association" "private-2a" {
  route_table_id = aws_route_table.private.id
  subnet_id      = aws_subnet.eu-west-2a-private.id
}

resource "aws_route_table_association" "public-2b" {
  route_table_id = aws_route_table.public.id
  subnet_id      = aws_subnet.eu-west-2b-public.id
}

resource "aws_route_table_association" "private-2b" {
  route_table_id = aws_route_table.private.id
  subnet_id      = aws_subnet.eu-west-2b-private.id
}

resource "aws_route_table_association" "public-2c" {
  route_table_id = aws_route_table.public.id
  subnet_id      = aws_subnet.eu-west-2c-public.id
}

resource "aws_route_table_association" "private-2c" {
  route_table_id = aws_route_table.private.id
  subnet_id      = aws_subnet.eu-west-2c-private.id
}

//resource "aws_vpc_endpoint" "secretsmanager" {
//  vpc_id = aws_vpc.six-degrees-of-youtube.id
//  service_name = "com.amazonaws.eu-west-2.secretsmanager"
//  subnet_ids = [
//    aws_subnet.eu-west-2a-private.id,
//    aws_subnet.eu-west-2b-private.id,
//    aws_subnet.eu-west-2c-private.id,
//  ]
//  security_group_ids = [
//    aws_security_group.web-rds.id
//  ]
//
//  tags = {
//    Name    = "six-degrees-of-youtube-secrets"
//    service = "six-degrees-of-youtube"
//  }
//}
