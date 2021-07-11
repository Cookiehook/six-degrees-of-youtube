resource "aws_vpc" "six-degrees-of-youtube" {
  assign_generated_ipv6_cidr_block = "false"
  cidr_block = "172.30.0.0/16"
  enable_dns_hostnames = "true"
  enable_dns_support = "true"
  instance_tenancy = "default"

  tags = {
    Name = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_security_group" "six-degrees-of-youtube" {
  name = "six-degrees-of-youtube"
  description = "SG used by all six-degrees-of-youtube resources"
  vpc_id = aws_vpc.six-degrees-of-youtube.id

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
    to_port  = "5432"
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
  tags = {
    Name    = "six-degrees-of-youtube"
    service = "six-degrees-of-youtube"
  }
}

// Subnets
resource "aws_subnet" "eu-west-2a-public" {
  vpc_id                          = aws_vpc.six-degrees-of-youtube.id
  availability_zone               = "eu-west-2a"
  cidr_block                      = "172.30.1.0/24"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a-public"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2a-private" {
  vpc_id                          = aws_vpc.six-degrees-of-youtube.id
  availability_zone               = "eu-west-2a"
  cidr_block                      = "172.30.2.0/24"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a-private"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2b-public" {
  vpc_id                          = aws_vpc.six-degrees-of-youtube.id
  availability_zone               = "eu-west-2b"
  cidr_block                      = "172.30.3.0/24"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2b-public"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_subnet" "eu-west-2b-private" {
  vpc_id                          = aws_vpc.six-degrees-of-youtube.id
  availability_zone               = "eu-west-2b"
  cidr_block                      = "172.30.4.0/24"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2b-private"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_eip" "six-degrees-of-youtube-eu-west-2a" {
  vpc = "true"
  network_border_group = "eu-west-2"
  public_ipv4_pool     = "amazon"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_eip" "six-degrees-of-youtube-eu-west-2b" {
  vpc = "true"
  network_border_group = "eu-west-2"
  public_ipv4_pool     = "amazon"

  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2b"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_nat_gateway" "six-degrees-of-youtube-eu-west-2a" {
  allocation_id     = aws_eip.six-degrees-of-youtube-eu-west-2a.id
  connectivity_type = "public"
  subnet_id         = aws_subnet.eu-west-2a-public.id
  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a"
    service = "six-degrees-of-youtube"
  }
}

resource "aws_nat_gateway" "six-degrees-of-youtube-eu-west-2b" {
  allocation_id     = aws_eip.six-degrees-of-youtube-eu-west-2b.id
  connectivity_type = "public"
  subnet_id         = aws_subnet.eu-west-2b-public.id
  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2b"
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
resource "aws_route_table" "six-degrees-of-youtube-public" {
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

resource "aws_route_table" "six-degrees-of-youtube-eu-west-2a-private" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.six-degrees-of-youtube-eu-west-2a.id
  }
  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2a-private"
    service = "six-degrees-of-youtube"

  }
}
resource "aws_route_table" "six-degrees-of-youtube-eu-west-2b-private" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.six-degrees-of-youtube-eu-west-2b.id
  }
  tags = {
    Name    = "six-degrees-of-youtube-eu-west-2b-private"
    service = "six-degrees-of-youtube"
  }
}

// Route Table associations with subnets / VPC
resource "aws_route_table_association" "eu-west-2a-private" {
  route_table_id = aws_route_table.six-degrees-of-youtube-eu-west-2a-private.id
  subnet_id      = aws_subnet.eu-west-2a-private.id
}

resource "aws_route_table_association" "eu-west-2b-private" {
  route_table_id = aws_route_table.six-degrees-of-youtube-eu-west-2b-private.id
  subnet_id      = aws_subnet.eu-west-2b-private.id
}

resource "aws_route_table_association" "eu-west-2a-public" {
  route_table_id = aws_route_table.six-degrees-of-youtube-public.id
  subnet_id      = aws_subnet.eu-west-2a-public.id
}

resource "aws_route_table_association" "eu-west-2b-public" {
  route_table_id = aws_route_table.six-degrees-of-youtube-public.id
  subnet_id      =  aws_subnet.eu-west-2b-public.id
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id = aws_vpc.six-degrees-of-youtube.id
  vpc_endpoint_type = "Interface"
  service_name = "com.amazonaws.eu-west-2.secretsmanager"
  private_dns_enabled = "true"
  subnet_ids = [
    aws_subnet.eu-west-2a-private.id,
    aws_subnet.eu-west-2b-private.id,
  ]
  security_group_ids = [
    aws_security_group.six-degrees-of-youtube.id
  ]

  tags = {
    Name    = "six-degrees-of-youtube-secrets"
    service = "six-degrees-of-youtube"
  }
}
