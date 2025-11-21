import base64
import json
import os
import datetime
from google.cloud import firestore
import functions_framework

db = firestore.Client()

@functions_framework.cloud_event
def process_task(cloud_event):
    """Triggered from a message on a Cloud Pub/Sub topic."""
    try:
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
        envelope = json.loads(pubsub_message)
        task_data = envelope.get("message")
        
        if not task_data:
            print("No task data found in envelope.")
            return

        print(f"Processing task: {task_data}")
        
        # Add metadata
        task_data['processed_at'] = datetime.datetime.now(datetime.timezone.utc)
        task_data['source_topic'] = 'lahin-tasks'
        
        # Calculate derived fields
        if 'Due_date' in task_data:
            try:
                due_date = datetime.datetime.fromisoformat(task_data['Due_date'].replace('Z', '+00:00'))
                now = datetime.datetime.now(datetime.timezone.utc)
                delta = due_date - now
                task_data['Due_in_hours'] = delta.total_seconds() / 3600
                task_data['Is_overdue'] = delta.total_seconds() < 0
            except ValueError:
                print("Invalid date format for Due_date")

        # Log to Firestore
        db.collection("tasks").add(task_data)
        print("Task logged to Firestore.")
        
    except Exception as e:
        print(f"Error processing task: {e}")
        raise e # Re-raise to trigger retry or DLQ
