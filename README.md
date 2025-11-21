# Deployment Guide

## Pre-requisites
1.  **GCP Project**: Ensure you have a GCP project with billing enabled.
2.  **Terraform**: Installed and authenticated.
3.  **SendGrid API Key**: Get your API key from [SendGrid Dashboard](https://app.sendgrid.com/settings/api_keys).

## Authentication
Authenticate with GCP:
```bash
gcloud auth application-default login
```

## Configuration
1.  Navigate to `infra/dev`:
    ```bash
    cd infra/dev
    ```

2.  Copy `terraform.tfvars.example` to `terraform.tfvars`:
    ```bash
    cp terraform.tfvars.example terraform.tfvars
    ```

3.  Edit `terraform.tfvars` and set your values:
    ```hcl
    project_id       = "your-gcp-project-id"
    region           = "asia-south1"
    resource_prefix  = "prod"  # Prefix for all resources
    sendgrid_api_key = "SG.xxxxxxxxxxxxxxxxxxxxx"  # Your actual SendGrid API key
    ```

## One-Command Deployment
Run the following commands:
```bash
terraform init
terraform apply
```

Type `yes` to confirm. Terraform will:
- ✅ Create all GCP resources (Pub/Sub, Cloud Functions, Firestore, Cloud Run, etc.)
- ✅ Create the Secret Manager secret with your SendGrid API key
- ✅ Configure all IAM permissions
- ✅ Set up Cloud Scheduler for daily reports

## Post-Deployment
**Access Client App** (private, requires authentication):
```bash
gcloud run services proxy ${resource_prefix}-client-app --project=your-project-id --region=asia-south1
```
Then open `http://localhost:8080`.

## Verify System
1.  Use the Client App to send test incidents and tasks
2.  Check Firestore collections: `incidents`, `tasks`, `escalations`
3.  Verify Cloud Scheduler job runs daily at 5:30 AM UTC
