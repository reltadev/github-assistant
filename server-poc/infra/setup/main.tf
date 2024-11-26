terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.68.0"
    }
  }
}

resource "aws_ecr_repository" "this" {
  name = "${var.app_name}"
}