variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "secret_id" {
  description = "The ID of the secret to create"
  type        = string
}

variable "secret_value" {
  description = "The actual secret value to store"
  type        = string
  sensitive   = true
}

resource "google_secret_manager_secret" "secret" {
  secret_id = var.secret_id
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "secret_version" {
  secret      = google_secret_manager_secret.secret.id
  secret_data = var.secret_value
}

output "secret_id" {
  value = google_secret_manager_secret.secret.id
}

output "secret_version_id" {
  value = google_secret_manager_secret_version.secret_version.id
}
