import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json
import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock google.cloud modules before importing main
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.pubsub_v1'] = MagicMock()
sys.modules['google.cloud.firestore'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['vertexai'] = MagicMock()
sys.modules['vertexai.generative_models'] = MagicMock()

# Mock functions_framework
mock_ff = MagicMock()
def mock_http(func):
    return func
def mock_cloud_event(func):
    return func
mock_ff.http = mock_http
mock_ff.cloud_event = mock_cloud_event
sys.modules['functions_framework'] = mock_ff

from pubsub_publisher.main import main as publisher_main
from incident_handler.main import process_incident, check_escalation
from daily_report.main import generate_report

class TestPublisher(unittest.TestCase):
    @patch('pubsub_publisher.main.publisher')
    def test_publisher_incident(self, mock_publisher):
        request = MagicMock()
        request.get_json.return_value = {'topic': 'lahin-incidents', 'message': {'id': '123'}}
        
        mock_future = MagicMock()
        mock_future.result.return_value = 'msg_id'
        mock_publisher.publish.return_value = mock_future
        
        response, status, headers = publisher_main(request)
        self.assertEqual(status, 200)
        self.assertIn('msg_id', response)

class TestIncidentHandler(unittest.TestCase):
    @patch('incident_handler.main.db')
    @patch('incident_handler.main.requests')
    @patch('incident_handler.main.os.getenv')
    def test_escalation_logic_trigger(self, mock_getenv, mock_requests, mock_db):
        mock_getenv.return_value = "dummy-key"
        # Mock 10 incidents within 10 minutes
        # Note: The logic in main.py uses query.stream()
        now = datetime.datetime.now(datetime.timezone.utc)
        incidents = []
        for i in range(10):
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {'service': 'api', 'region': 'us'}
            incidents.append(mock_doc)
        
        mock_db.collection.return_value.where.return_value.stream.return_value = incidents
        
        check_escalation()
        
        # Should trigger email via requests.post
        mock_requests.post.assert_called()
        # Should add to escalations
        mock_db.collection.return_value.add.assert_called()

class TestDailyReport(unittest.TestCase):
    @patch('daily_report.main.db')
    @patch('daily_report.main.storage_client')
    @patch('daily_report.main.GenerativeModel')
    @patch('daily_report.main.requests')
    @patch('daily_report.main.os.getenv')
    def test_generate_report(self, mock_getenv, mock_requests, mock_gen_model, mock_storage, mock_db):
        mock_getenv.return_value = "dummy-key"
        # Mock Firestore data
        mock_db.collection.return_value.where.return_value.stream.return_value = []
        
        # Mock Gemini response
        mock_model_instance = MagicMock()
        mock_model_instance.generate_content.return_value.text = "Daily Summary Content"
        mock_gen_model.return_value = mock_model_instance
        
        response, status = generate_report(MagicMock())
        
        self.assertEqual(status, 200)
        # Verify GCS upload
        mock_storage.bucket.return_value.blob.return_value.upload_from_string.assert_called_with("Daily Summary Content")
        # Verify Email
        mock_requests.post.assert_called()

if __name__ == '__main__':
    unittest.main()
