"""Integration tests for Web Server HTTP Endpoints."""

import unittest
import threading
import time
import urllib.request
import json
import http.server
from web_server import GameHTTPRequestHandler


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8099
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", cls.port), GameHTTPRequestHandler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_start_game_and_guess_flow(self):
        url = f"http://127.0.0.1:{self.port}/api/start-game"
        payload = json.dumps({"username": "TestPlayer", "difficulty": "Easy"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertIn("session_id", data)
            self.assertEqual(data["difficulty"], "Easy")
            session_id = data["session_id"]

        # Make a guess
        guess_url = f"http://127.0.0.1:{self.port}/api/guess"
        guess_payload = json.dumps({"session_id": session_id, "guess": 25}).encode("utf-8")
        guess_req = urllib.request.Request(guess_url, data=guess_payload, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(guess_req) as resp:
            guess_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(guess_data["status"], "success")
            self.assertIn("hint", guess_data)
            self.assertIn("meta", guess_data)

    def test_leaderboard_endpoint(self):
        url = f"http://127.0.0.1:{self.port}/api/leaderboard"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertIsInstance(data["leaderboard"], list)

    def test_stats_endpoint(self):
        url = f"http://127.0.0.1:{self.port}/api/stats?username=TestPlayer"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["player"]["username"], "TestPlayer")


if __name__ == "__main__":
    unittest.main()
