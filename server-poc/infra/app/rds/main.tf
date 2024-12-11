resource "aws_security_group" "rds" {
  name   = "${var.app_name}-rds-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "rds" {
  name       = "${var.app_name}-rds-subnet-group"
  subnet_ids = var.private_subnet_ids
}

resource "aws_secretsmanager_secret" "rds_credentials" {
  name = "${var.app_name}-rds-credentials"
}

resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id = aws_secretsmanager_secret.rds_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

resource "aws_db_instance" "postgres" {
  identifier        = "${var.app_name}-postgres"
  engine            = "postgres"
  engine_version    = "15.5"
  instance_class    = "db.r6g.large"
  allocated_storage = 200

  db_name  = "github_assistant"
  username = jsondecode(aws_secretsmanager_secret_version.rds_credentials.secret_string)["username"]
  password = jsondecode(aws_secretsmanager_secret_version.rds_credentials.secret_string)["password"]

  parameter_group_name = aws_db_parameter_group.postgres.name

  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  skip_final_snapshot = true
  
  backup_retention_period = 7
  multi_az               = false
}

resource "aws_db_parameter_group" "postgres" {
  family = "postgres15"
  name   = "${var.app_name}-postgres-params"

  parameter {
    name  = "timezone"
    value = "UTC"
  }

  parameter {
    name  = "client_encoding"
    value = "UTF8"
  }
} 