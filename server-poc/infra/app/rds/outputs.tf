output "rds_endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "rds_port" {
  value = aws_db_instance.postgres.port
} 