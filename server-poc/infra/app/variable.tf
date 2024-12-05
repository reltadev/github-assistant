variable "app_name" {
  description = "Name of the app."
  type        = string
}
variable "region" {
  description = "AWS region to deploy the network to."
  type        = string
}
variable "image" {
  description = "Image used to start the container. Should be in repository-url/image:tag format."
  type        = string
}
variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}