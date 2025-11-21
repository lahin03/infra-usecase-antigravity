# Deployment Guide

## Pre-requisites
1.  **GCP Project**: Ensure you have a GCP project with billing enabled.
2.  **Terraform**: Installed and authenticated (`gcloud auth application-default login`).
3.  **SendGrid API Key**: You will need a SendGrid API key for email notifications.

## Configuration
1.  Navigate to `infra/dev`.
2.  Copy `terraform.tfvars.example` to `terraform.tfvars`.
3.  Edit `terraform.tfvars` and set your values:
    ```hcl
    project_id      = "your-project-id"
    region          = "asia-south1"
    resource_prefix = "prod" # This will prefix all resources (e.g., prod-incidents, prod-client-app)
    ```

## Deployment
1.  Initialize Terraform:
    ```bash
    terraform init
    ```
2.  Apply the configuration:
    ```bash
    terraform apply
    ```
    Type `yes` to confirm.

## Post-Deployment Steps
1.  **Add Secret**: The deployment creates a Secret Manager secret named `${resource_prefix}-sendgrid-api-key`.
    -   Go to GCP Console > Security > Secret Manager.
    -   Find the secret (e.g., `prod-sendgrid-api-key`).
    -   Add a new version with your actual SendGrid API Key as the value.
    -   **Note**: The Cloud Functions will pick up the `latest` version.

2.  **Access Client App**:
    -   The Cloud Run service `${resource_prefix}-client-app` is deployed **privately** (no `allUsers` access).
    -   To access it, you must have the `roles/run.invoker` permission.
    -   You can use `gcloud run services proxy` to access it locally:
        ```bash
        gcloud run services proxy ${resource_prefix}-client-app --project=your-project-id --region=asia-south1
        ```
        Then open `http://localhost:8080`.

3.  **Verify System**:
    -   Use the Client App to send events.
    -   Check Pub/Sub topics and Firestore collections.
    -   Check Cloud Scheduler for the daily report job.
