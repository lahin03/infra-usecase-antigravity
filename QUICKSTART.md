# Quick Start - One-Command Deployment

## What You Need
1. **SendGrid API Key**: Get it from https://app.sendgrid.com/settings/api_keys
2. **GCP Project ID**: Your Google Cloud project ID

## Steps

### 1. Authenticate
```bash
gcloud auth application-default login
```

### 2. Configure
```bash
cd infra/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id       = "your-actual-project-id"
region           = "asia-south1"
resource_prefix  = "prod"
sendgrid_api_key = "SG.your-actual-sendgrid-key"
```

### 3. Deploy Everything
```bash
terraform init
terraform apply
```

Type `yes` when prompted. That's it! ✅

## What Gets Created
- ✅ All Cloud Functions (API Facade, Incident Handler, Task Handler, Daily Report)
- ✅ Pub/Sub topics and subscriptions
- ✅ Firestore database
- ✅ Cloud Run client app
- ✅ Cloud Scheduler (daily reports at 5:30 AM UTC)
- ✅ Secret Manager secret with your SendGrid API key
- ✅ All IAM service accounts and permissions
- ✅ Cloud Storage buckets

## Access the Client App
```bash
gcloud run services proxy prod-client-app --project=your-project-id --region=asia-south1
```
Then open http://localhost:8080
