provider "google" {
  project = var.project_id
  region  = var.region
}

# --- IAM ---
module "iam" {
  source     = "../modules/iam"
  project_id = var.project_id

  service_accounts = {
    "${var.resource_prefix}-client-app-sa"       = "SA for Client App"
    "${var.resource_prefix}-pubsub-publisher-sa" = "SA for Backend Function"
    "${var.resource_prefix}-incident-handler-sa" = "SA for Incident Handler"
    "${var.resource_prefix}-task-handler-sa"     = "SA for Task Handler"
    "${var.resource_prefix}-daily-report-sa"     = "SA for Daily Report"
    "${var.resource_prefix}-scheduler-sa"        = "SA for Scheduler"
  }

  project_roles = {
    "${var.resource_prefix}-client-app-sa"       = ["roles/run.invoker"] # To invoke pubsub-publisher
    "${var.resource_prefix}-pubsub-publisher-sa" = ["roles/pubsub.publisher"]
    "${var.resource_prefix}-incident-handler-sa" = ["roles/datastore.user", "roles/secretmanager.secretAccessor"]
    "${var.resource_prefix}-task-handler-sa"     = ["roles/datastore.user"]
    "${var.resource_prefix}-daily-report-sa"     = ["roles/datastore.user", "roles/aiplatform.user", "roles/storage.objectCreator", "roles/secretmanager.secretAccessor"]
    "${var.resource_prefix}-scheduler-sa"        = ["roles/run.invoker"] # To invoke daily-report
  }
}

# --- Pub/Sub ---
module "pubsub" {
  source     = "../modules/pubsub"
  project_id = var.project_id
  topics = {
    incident = { name = "${var.resource_prefix}-incidents" }
    task     = { name = "${var.resource_prefix}-tasks" }
  }
  dead_letter_topic = "${var.resource_prefix}-dead-letter-topic"
}

# --- Firestore ---
module "firestore" {
  source     = "../modules/firestore"
  project_id = var.project_id
  region     = var.region
}

# --- Secret Manager ---
module "secrets" {
  source       = "../modules/secret_manager"
  project_id   = var.project_id
  secret_id    = "${var.resource_prefix}-sendgrid-api-key"
  secret_value = var.sendgrid_api_key
}

# --- Cloud Storage ---
module "storage" {
  source      = "../modules/cloud_storage"
  project_id  = var.project_id
  bucket_name = "${var.resource_prefix}-daily-report-bucket-${var.project_id}" # Unique bucket name
  location    = "ASIA-SOUTH1"
}

# --- Cloud Functions Source Bucket ---
resource "google_storage_bucket" "function_source" {
  name     = "${var.resource_prefix}-${var.project_id}-function-source"
  location = var.region
}

# --- Cloud Functions ---

# 1. API Facade (pubsub-publisher)
module "pubsub_publisher" {
  source                = "../modules/cloud_functions"
  project_id            = var.project_id
  region                = var.region
  function_name         = "${var.resource_prefix}-pubsub-publisher"
  source_dir            = "../../src/pubsub_publisher"
  bucket_name           = google_storage_bucket.function_source.name
  entry_point           = "main"
  service_account_email = module.iam.emails["${var.resource_prefix}-pubsub-publisher-sa"]
  trigger_http          = true

  environment_variables = {
    INCIDENT_TOPIC = module.pubsub.topic_names["incident"]
    TASK_TOPIC     = module.pubsub.topic_names["task"]
    PROJECT_ID     = var.project_id
  }
}

# 2. Incident Handler
module "incident_handler" {
  source                = "../modules/cloud_functions"
  project_id            = var.project_id
  region                = var.region
  function_name         = "${var.resource_prefix}-incident-handler"
  source_dir            = "../../src/incident_handler"
  bucket_name           = google_storage_bucket.function_source.name
  entry_point           = "process_incident"
  service_account_email = module.iam.emails["${var.resource_prefix}-incident-handler-sa"]

  event_trigger = {
    event_type   = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = module.pubsub.topic_ids["incident"]
    retry_policy = "RETRY_POLICY_RETRY"
  }

  secret_environment_variables = [
    {
      key        = "SENDGRID_API_KEY"
      project_id = var.project_id
      secret     = module.secrets.secret_id
      version    = "latest"
    }
  ]

  depends_on = [module.secrets]
}

# 3. Task Handler
module "task_handler" {
  source                = "../modules/cloud_functions"
  project_id            = var.project_id
  region                = var.region
  function_name         = "${var.resource_prefix}-task-handler"
  source_dir            = "../../src/task_handler"
  bucket_name           = google_storage_bucket.function_source.name
  entry_point           = "process_task"
  service_account_email = module.iam.emails["${var.resource_prefix}-task-handler-sa"]

  event_trigger = {
    event_type   = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic = module.pubsub.topic_ids["task"]
    retry_policy = "RETRY_POLICY_RETRY"
  }
}

# 4. Daily Report
module "daily_report" {
  source                = "../modules/cloud_functions"
  project_id            = var.project_id
  region                = var.region
  function_name         = "${var.resource_prefix}-daily-report"
  source_dir            = "../../src/daily_report"
  bucket_name           = google_storage_bucket.function_source.name
  entry_point           = "generate_report"
  service_account_email = module.iam.emails["${var.resource_prefix}-daily-report-sa"]
  trigger_http          = true # Triggered by Scheduler via HTTP

  environment_variables = {
    PROJECT_ID  = var.project_id
    BUCKET_NAME = module.storage.bucket_name
  }

  secret_environment_variables = [
    {
      key        = "SENDGRID_API_KEY"
      project_id = var.project_id
      secret     = module.secrets.secret_id
      version    = "latest"
    }
  ]

  depends_on = [module.secrets]
}

# --- Cloud Run (Client App) ---
module "client_app" {
  source                = "../modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  service_name          = "${var.resource_prefix}-client-app"
  image                 = "asia-south1-docker.pkg.dev/sada-seed-2025-sandbox/cloud-run-images/lahin-pubsub-frontend:latest" # Placeholder image
  service_account_email = module.iam.emails["${var.resource_prefix}-client-app-sa"]
}

# --- Cloud Scheduler ---
module "scheduler" {
  source                = "../modules/cloud_scheduler"
  project_id            = var.project_id
  region                = var.region
  job_name              = "${var.resource_prefix}-daily-report-scheduler"
  target_uri            = module.daily_report.function_uri
  service_account_email = module.iam.emails["${var.resource_prefix}-scheduler-sa"]
}
