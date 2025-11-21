variable "project_id" {
  description = "The project ID to deploy to"
  type        = string
}

variable "region" {
  description = "The region to deploy to"
  type        = string
  default     = "us-central1"
}

variable "function_name" {
  description = "Name of the Cloud Function"
  type        = string
}

variable "entry_point" {
  description = "Entry point of the function"
  type        = string
  default     = "main"
}

variable "source_dir" {
  description = "Path to the source code directory"
  type        = string
}

variable "bucket_name" {
  description = "Name of the GCS bucket to store source code"
  type        = string
}

variable "environment_variables" {
  description = "Environment variables for the function"
  type        = map(string)
  default     = {}
}

variable "trigger_http" {
  description = "Whether to trigger via HTTP"
  type        = bool
  default     = false
}

variable "event_trigger" {
  description = "Event trigger configuration"
  type = object({
    event_type   = string
    pubsub_topic = string
    retry_policy = string
  })
  default = null
}

data "archive_file" "source" {
  type        = "zip"
  source_dir  = var.source_dir
  output_path = "/tmp/${var.function_name}.zip"
}

resource "google_storage_bucket_object" "archive" {
  name   = "${var.function_name}-${data.archive_file.source.output_md5}.zip"
  bucket = var.bucket_name
  source = data.archive_file.source.output_path
}

variable "service_account_email" {
  description = "The service account to run the function as"
  type        = string
}

variable "secret_environment_variables" {
  description = "List of secret environment variables"
  type = list(object({
    key        = string
    project_id = string
    secret     = string
    version    = string
  }))
  default = []
}

resource "google_cloudfunctions2_function" "function" {
  name        = var.function_name
  location    = var.region
  description = "Managed by Terraform"

  build_config {
    runtime     = "python310"
    entry_point = var.entry_point
    source {
      storage_source {
        bucket = var.bucket_name
        object = google_storage_bucket_object.archive.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    available_memory      = "256M"
    timeout_seconds       = 60
    environment_variables = var.environment_variables
    service_account_email = var.service_account_email

    dynamic "secret_environment_variables" {
      for_each = var.secret_environment_variables
      content {
        key        = secret_environment_variables.value.key
        project_id = secret_environment_variables.value.project_id
        secret     = secret_environment_variables.value.secret
        version    = secret_environment_variables.value.version
      }
    }
  }

  # Dynamic block for event trigger if provided
  dynamic "event_trigger" {
    for_each = var.event_trigger != null ? [var.event_trigger] : []
    content {
      event_type   = event_trigger.value.event_type
      pubsub_topic = event_trigger.value.pubsub_topic
      retry_policy = event_trigger.value.retry_policy
    }
  }
}

output "function_uri" {
  value = google_cloudfunctions2_function.function.service_config[0].uri
}
