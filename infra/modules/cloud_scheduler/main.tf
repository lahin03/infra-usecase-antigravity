variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "region" {
  description = "The region to deploy to"
  type        = string
  default     = "asia-south1"
}

variable "job_name" {
  description = "Name of the scheduler job"
  type        = string
}

variable "schedule" {
  description = "Cron schedule"
  type        = string
  default     = "30 5 * * *"
}

variable "target_uri" {
  description = "The URI of the target Cloud Function"
  type        = string
}

variable "service_account_email" {
  description = "Service account email to invoke the target"
  type        = string
}

resource "google_cloud_scheduler_job" "job" {
  name             = var.job_name
  region           = var.region
  project          = var.project_id
  schedule         = var.schedule
  time_zone        = "UTC"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = var.target_uri
    
    oidc_token {
      service_account_email = var.service_account_email
    }
  }
}
