import os
import json
import datetime
import requests
from google.cloud import firestore
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel
import functions_framework

db = firestore.Client()
storage_client = storage.Client()

PROJECT_ID = os.getenv('PROJECT_ID')
BUCKET_NAME = os.getenv('BUCKET_NAME')

def send_email(subject, body):
    """Sends an email using SendGrid API."""
    api_key = os.getenv('SENDGRID_API_KEY')
    if not api_key:
        print("SendGrid API key missing.")
        return

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "personalizations": [{"to": [{"email": "lahin.saleem@sada.com"}]}],
        "from": {"email": "report@example.com"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }
    requests.post(url, headers=headers, json=data)

@functions_framework.http
def generate_report(request):
    """Generates daily summary using Gemini."""
    print("Starting daily report generation...")
    
    # 1. Query Data
    tasks_ref = db.collection("tasks").where("Status", "==", "PENDING")
    pending_tasks = [d.to_dict() for d in tasks_ref.stream()]
    
    now = datetime.datetime.now(datetime.timezone.utc)
    yesterday = now - datetime.timedelta(days=1)
    escalations_ref = db.collection("escalations").where("detected_at", ">=", yesterday)
    recent_escalations = [d.to_dict() for d in escalations_ref.stream()]
    
    # 2. Generate Prompt
    prompt = f"""
    You are a daily operations report generator.
    
    Pending Tasks:
    {json.dumps(pending_tasks, default=str)}
    
    Recent Escalations (Last 24h):
    {json.dumps(recent_escalations, default=str)}
    
    Please generate a concise, professional daily summary for the Tech Lead.
    Highlight urgent items and provide metrics.
    """
    
    # 3. Call Gemini
    try:
        vertexai.init(project=PROJECT_ID, location="asia-south1")
        model = GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        summary_text = response.text
        print("✅ Vertex AI summary generated successfully")
    except Exception as e:
        print(f"Gemini API Error: {e}")
        summary_text = "Failed to generate AI summary. Please check raw logs."

    # 4. Archive to GCS
    filename = f"daily-report-{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(summary_text)
    print(f"Report archived to {BUCKET_NAME}/{filename}")
    
    # 5. Email
    send_email(f"Daily Summary - {now.strftime('%Y-%m-%d')}", summary_text)
    print("Daily Summary sent succesfully")
    
    return "Report generated", 200
