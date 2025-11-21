import os
import json
import requests
from flask import Flask, render_template_string, request, jsonify
import google.auth.transport.requests
import google.oauth2.id_token

app = Flask(__name__)

# Configuration
PUBSUB_PUBLISHER_URL = os.environ.get("PUBSUB_PUBLISHER_URL", "https://asia-south1-sada-seed-2025-sandbox.cloudfunctions.net/lahin-pubsub-publisher")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Event Automation Demo</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { border: 1px solid #ccc; padding: 20px; margin-bottom: 20px; border-radius: 5px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background-color: #4285f4; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background-color: #357ae8; }
        #response { margin-top: 20px; padding: 10px; background-color: #f0f0f0; display: none; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>Event Automation Demo</h1>
    
    <div class="card">
        <h2>Report Incident</h2>
        <form id="incidentForm">
            <div class="form-group">
                <label>Incident ID</label>
                <input type="text" name="incident_id" value="INC-001">
            </div>
            <div class="form-group">
                <label>Service</label>
                <input type="text" name="service" value="billing-api">
            </div>
            <div class="form-group">
                <label>Severity</label>
                <select name="severity">
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                </select>
            </div>
            <div class="form-group">
                <label>Region</label>
                <input type="text" name="region" value="asia-south1">
            </div>
            <button type="submit">Submit Incident</button>
        </form>
    </div>

    <div class="card">
        <h2>Create Task</h2>
        <form id="taskForm">
            <div class="form-group">
                <label>Task ID</label>
                <input type="text" name="Task_id" value="TSK-001">
            </div>
            <div class="form-group">
                <label>Title</label>
                <input type="text" name="Title" value="Review Logs">
            </div>
            <div class="form-group">
                <label>Assigned To</label>
                <input type="email" name="Assigned_to" value="dev@example.com">
            </div>
            <div class="form-group">
                <label>Due Date</label>
                <input type="datetime-local" name="Due_date">
            </div>
            <button type="submit">Create Task</button>
        </form>
    </div>

    <div id="response"></div>

    <script>
        async def submit(type, data) {
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.innerHTML = 'Sending...';
            
            try {
                const res = await fetch('/publish', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type, data})
                });
                const result = await res.json();
                responseDiv.innerHTML = `<span class="${result.success ? 'success' : 'error'}">${JSON.stringify(result, null, 2)}</span>`;
            } catch (e) {
                responseDiv.innerHTML = `<span class="error">Error: ${e.message}</span>`;
            }
        }

        document.getElementById('incidentForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            submit('incident', data);
        });

        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            submit('task', data);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/publish', methods=['POST'])
def publish():
    data = request.json
    msg_type = data.get('type')
    payload = data.get('data')
    
    topic_map = {
        'incident': 'lahin-incidents',
        'task': 'lahin-tasks'
    }
    
    topic = topic_map.get(msg_type)
    if not topic:
        return jsonify({"success": False, "error": "Invalid type"}), 400

    # Authenticate request to Cloud Function
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, PUBSUB_PUBLISHER_URL)
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }
    
    body = {
        "topic": topic,
        "message": payload,
        "userToken": "demo-user-token"
    }
    
    try:
        resp = requests.post(PUBSUB_PUBLISHER_URL, headers=headers, json=body)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
