import base64
import json
import os
import datetime
import requests
from google.cloud import firestore
import functions_framework

db = firestore.Client()

def send_email(subject, body):
    """Sends an email using SendGrid API."""
    api_key = os.getenv('SENDGRID_API_KEY')
    if not api_key:
        print("SendGrid API key missing. Skipping email.")
        return

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": "lahin.saleem@sada.com"}]}],
        "from": {"email": "alert@example.com"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in [200, 202]:
            print("✅ Escalation email sent successfully!")
        else:
            print(f"⚠️ Failed to send email: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@functions_framework.cloud_event
def process_incident(cloud_event):
    """Triggered from a message on a Cloud Pub/Sub topic."""
    try:
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        envelope = json.loads(pubsub_message)
        incident_data = envelope.get("message")
        
        if not incident_data:
            print("No incident data found.")
            return

        print(f"Processing incident: {incident_data}")
        
        # Add metadata
        incident_data['logged_at'] = datetime.datetime.now(datetime.timezone.utc)
        
        # Log to Firestore
        db.collection("incidents").add(incident_data)
        print("Successfully written incident to Firestore.")
        
        check_escalation()
        
    except Exception as e:
        print(f"Error processing incident: {e}")
        raise e

def check_escalation():
    """Checks if >10 incidents happened in the last 10 minutes."""
    incidents_ref = db.collection("incidents")
    
    # Query last 10 minutes
    now = datetime.datetime.now(datetime.timezone.utc)
    ten_mins_ago = now - datetime.timedelta(minutes=10)
    
    # Note: This requires a composite index on logged_at DESC
    # For simplicity in this demo, we query recent logs and filter in memory if needed, 
    # but ideally we use a range filter.
    query = incidents_ref.where("logged_at", ">=", ten_mins_ago)
    results = list(query.stream())
    
    count = len(results)
    print(f"Found {count} incidents in the last 10 minutes.")
    
    if count >= 10:
        print(f"🚨 Escalation: {count} incidents logged in < 10 minutes.")
        
        escalation_id = f"ESC-{now.strftime('%Y%m%d-%H%M%S')}"
        escalation_data = {
            "escalation_id": escalation_id,
            "trigger_reason": "10+ incidents within 10 minutes",
            "total_incidents": count,
            "detected_at": now,
            "status": "ACTIVE",
            "summary": {
                "affected_services": list(set(d.to_dict().get('service', 'unknown') for d in results)),
                "regions_involved": list(set(d.to_dict().get('region', 'unknown') for d in results))
            }
        }
        
        db.collection("escalations").add(escalation_data)
        send_email("🚨 Escalation Alert", f"High incident rate detected.\n\n{json.dumps(escalation_data, indent=2, default=str)}")
