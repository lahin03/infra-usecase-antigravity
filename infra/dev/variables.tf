variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
  default     = "my-gcp-project-id" 
}

variable "region" {
  description = "The region to deploy to"
  type        = string
  default     = "us-central1"
}
variable "resource_prefix" {
  description = "Prefix to add to all resource names"
  type        = string
  default     = "prod"
}
