import os
import json
import base64
from google.cloud import pubsub_v1
import functions_framework

publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.getenv('PROJECT_ID')
INCIDENT_TOPIC = os.getenv('INCIDENT_TOPIC')
TASK_TOPIC = os.getenv('TASK_TOPIC')

@functions_framework.http
def main(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`.
    """
    # CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    request_json = request.get_json(silent=True)
    
    if not request_json:
        return ('Invalid JSON', 400, headers)

    topic_name = request_json.get('topic')
    message_data = request_json.get('message')
    user_token = request_json.get('userToken', 'anonymous')
    
    if not topic_name or not message_data:
        return ('Missing topic or message field', 400, headers)

    # Wrap message in envelope
    envelope = {
        "message": message_data,
        "user_token_preview": user_token[:10] + "..." if user_token else None,
        "source": "web-frontend"
    }
    
    data_str = json.dumps(envelope).encode("utf-8")
    
    try:
        if topic_name == 'lahin-incidents':
            topic_path = publisher.topic_path(PROJECT_ID, INCIDENT_TOPIC)
            future = publisher.publish(topic_path, data_str)
            msg_id = future.result()
            return (json.dumps({"success": True, "messageId": msg_id, "topic": topic_name}), 200, headers)
            
        elif topic_name == 'lahin-tasks':
            topic_path = publisher.topic_path(PROJECT_ID, TASK_TOPIC)
            future = publisher.publish(topic_path, data_str)
            msg_id = future.result()
            return (json.dumps({"success": True, "messageId": msg_id, "topic": topic_name}), 200, headers)
            
        else:
            return (f'Unknown topic: {topic_name}', 400, headers)
            
    except Exception as e:
        print(f"Error publishing message: {e}")
        return (f"Internal Server Error: {e}", 500, headers)
