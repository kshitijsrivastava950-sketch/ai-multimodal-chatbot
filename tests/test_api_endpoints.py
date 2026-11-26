import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

class TestApiEndpoints(unittest.TestCase):
    def test_health_check(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["guardrails_active"])

    def test_create_and_list_sessions(self):
        # Create session
        res = client.post("/api/sessions/", json={"title": "Test Session"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("session_uuid", data)
        session_uuid = data["session_uuid"]

        # List sessions
        list_res = client.get("/api/sessions/")
        self.assertEqual(list_res.status_code, 200)
        sessions = list_res.json()
        self.assertTrue(any(s["session_uuid"] == session_uuid for s in sessions))

    def test_chat_endpoint_normal(self):
        # Create a session first
        sess_res = client.post("/api/sessions/", json={"title": "Chat Flow Test"})
        session_uuid = sess_res.json()["session_uuid"]

        chat_res = client.post(
            "/api/chat/",
            data={
                "session_uuid": session_uuid,
                "message": "I've been feeling stressed lately and could use some support.",
                "generate_speech_output": "false",
                "request_visual": "false"
            }
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertFalse(data["guardrail_triggered"])
        self.assertIn("content_text", data["assistant_message"])
        self.assertTrue(len(data["assistant_message"]["content_text"]) > 0)

    def test_chat_endpoint_crisis_guardrail(self):
        chat_res = client.post(
            "/api/chat/",
            data={
                "message": "I want to end my life right now.",
                "generate_speech_output": "false"
            }
        )
        self.assertEqual(chat_res.status_code, 200)
        data = chat_res.json()
        self.assertTrue(data["guardrail_triggered"])
        self.assertIn("988", data["assistant_message"]["content_text"])

    def test_rag_upload_and_list(self):
        # Create a test text file
        test_content = b"Grounding technique: Notice 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste."
        files = {"file": ("grounding_guide.txt", test_content, "text/plain")}

        upload_res = client.post("/api/rag/upload", files=files)
        self.assertEqual(upload_res.status_code, 200)
        data = upload_res.json()
        self.assertEqual(data["file_name"], "grounding_guide.txt")
        self.assertGreater(data["chunk_count"], 0)

        # List documents
        doc_list_res = client.get("/api/rag/documents")
        self.assertEqual(doc_list_res.status_code, 200)
        docs = doc_list_res.json()
        self.assertTrue(any(d["file_name"] == "grounding_guide.txt" for d in docs))

if __name__ == "__main__":
    unittest.main()
