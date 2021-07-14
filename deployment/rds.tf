resource "random_password" "master" {
  length            = 40
  special           = true
  min_special       = 5
  override_special  = "!#$%^&*()-_=+[]{}<>:?"
}

resource "aws_db_subnet_group" "rds" {
  name = "default-rds-subnet-group"
  subnet_ids = [
    aws_subnet.eu-west-2a-public.id,
    aws_subnet.eu-west-2a-private.id,
    aws_subnet.eu-west-2b-public.id,
    aws_subnet.eu-west-2b-private.id,
  ]
}

resource "aws_db_instance" "six-degrees-of-youtube" {
  allocated_storage                     = "20"
  auto_minor_version_upgrade            = "true"
  availability_zone                     = "eu-west-2a"
  backup_retention_period               = "7"
  backup_window                         = "03:00-03:30"
  ca_cert_identifier                    = "rds-ca-2019"
  copy_tags_to_snapshot                 = "true"
  db_subnet_group_name                  = aws_db_subnet_group.rds.name
  deletion_protection                   = "false"
  engine                                = "postgres"
  engine_version                        = "12.5"
  iam_database_authentication_enabled   = "false"
  identifier                            = "six-degrees-of-youtube"
  instance_class                        = "db.t2.micro"
  iops                                  = "0"
  license_model                         = "postgresql-license"
  maintenance_window                    = "mon:23:58-tue:00:28"
  max_allocated_storage                 = "1000"
  monitoring_interval                   = "60"
  monitoring_role_arn                   = data.aws_iam_role.rds-monitoring.arn
  multi_az                              = "false"
  option_group_name                     = "default:postgres-12"
  parameter_group_name                  = "default.postgres12"
  performance_insights_enabled          = "false"
  performance_insights_retention_period = "0"
  port                                  = "5432"
  publicly_accessible                   = "false"
  storage_encrypted                     = "false"
  storage_type                          = "gp2"
  username                              = "postgres"
  password                              = random_password.master.result
  vpc_security_group_ids                = [aws_security_group.six-degrees-of-youtube.id]
  skip_final_snapshot                   = "true"
}


resource "aws_secretsmanager_secret" "password" {
  name = "six_degrees_of_youtube_db_dsn"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "password" {
  secret_id = aws_secretsmanager_secret.password.id
  secret_string = "postgresql://${aws_db_instance.six-degrees-of-youtube.username}:${random_password.master.result}@${aws_route53_record.rds.fqdn}:${aws_db_instance.six-degrees-of-youtube.port}"
}
