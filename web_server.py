"""Zero-dependency HTTP Web Server for Guess the Number Game.

Uses Python standard library's http.server with REST API endpoints and static file serving.
"""

import http.server
import json
import os
import sys
import urllib.parse
from datetime import datetime
from database import Database
from game_logic import GameEngine
from models import Difficulty, DifficultyConfig

# Ensure stdout/stderr handles UTF-8 smoothly across Windows, Linux, and Docker
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Active sessions store in-memory (keyed by session ID)
ACTIVE_SESSIONS = {}


class GameHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    db = Database("game.db")
    web_dir = os.path.dirname(os.path.abspath(__file__))

    def _send_json(self, data: dict, status_code: int = 200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/leaderboard":
            limit = int(query.get("limit", [10])[0])
            rows = self.db.get_leaderboard(limit=limit)
            self._send_json({"status": "success", "leaderboard": rows})
            return

        elif path == "/api/stats":
            username = query.get("username", [""])[0]
            if not username:
                stats = self.db.get_overall_stats()
                self._send_json({"status": "success", "overall": stats})
            else:
                player = self.db.get_or_create_player(username)
                stats = self.db.get_player_stats(player.id)
                recent = self.db.get_player_games(player.id, limit=5)
                self._send_json({
                    "status": "success",
                    "player": {"id": player.id, "username": player.username},
                    "stats": stats.__dict__ if stats else None,
                    "recent_games": recent
                })
            return

        elif path == "/" or path == "/index.html":
            html_file = os.path.join(self.web_dir, "templates", "index.html")
            if os.path.exists(html_file):
                with open(html_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Serve static assets
        if path.startswith("/static/"):
            rel_path = path.lstrip("/")
            file_path = os.path.join(self.web_dir, rel_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = "text/plain"
                if file_path.endswith(".css"):
                    content_type = "text/css"
                elif file_path.endswith(".js"):
                    content_type = "application/javascript"
                elif file_path.endswith(".png"):
                    content_type = "image/png"
                elif file_path.endswith(".svg"):
                    content_type = "image/svg+xml"

                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {}

        if path == "/api/start-game":
            username = payload.get("username", "Guest").strip() or "Guest"
            difficulty_str = payload.get("difficulty", "Medium")
            custom_cfg = None

            if difficulty_str.lower() == "custom":
                min_v = int(payload.get("min_val", 1))
                max_v = int(payload.get("max_val", 100))
                max_a = int(payload.get("max_attempts", 7))
                custom_cfg = DifficultyConfig(
                    min_val=min_v,
                    max_val=max_v,
                    max_attempts=max_a,
                    base_points=int((max_v - min_v) * 1.5)
                )
                difficulty = Difficulty.CUSTOM
            else:
                difficulty = Difficulty.from_string(difficulty_str)

            player = self.db.get_or_create_player(username)
            engine = GameEngine(difficulty=difficulty, custom_config=custom_cfg)
            
            session_id = f"{player.id}_{int(datetime.now().timestamp() * 1000)}"
            ACTIVE_SESSIONS[session_id] = {
                "player_id": player.id,
                "engine": engine
            }

            self._send_json({
                "status": "success",
                "session_id": session_id,
                "difficulty": engine.difficulty.value,
                "min_val": engine.min_bound,
                "max_val": engine.max_bound,
                "max_attempts": engine.max_attempts,
                "username": player.username
            })
            return

        elif path == "/api/guess":
            session_id = payload.get("session_id")
            if not session_id or session_id not in ACTIVE_SESSIONS:
                self._send_json({"status": "error", "message": "Session expired or invalid."}, 400)
                return

            session_data = ACTIVE_SESSIONS[session_id]
            engine: GameEngine = session_data["engine"]
            player_id = session_data["player_id"]

            try:
                guess = int(payload.get("guess"))
            except (ValueError, TypeError):
                self._send_json({"status": "error", "message": "Invalid guess format. Number required."}, 400)
                return

            is_correct, hint_msg, meta = engine.check_guess(guess)
            
            game_id = None
            if engine.is_game_over:
                record = engine.to_game_record(player_id)
                game_id = self.db.save_game(record)
                # Cleanup session
                del ACTIVE_SESSIONS[session_id]

            self._send_json({
                "status": "success",
                "is_correct": is_correct,
                "hint": hint_msg,
                "meta": meta,
                "game_id": game_id,
                "is_game_over": engine.is_game_over,
                "is_won": engine.is_won,
                "target_number": engine.target_number if engine.is_game_over else None,
                "score": meta.get("score", 0)
            })
            return

        self.send_error(404, "Endpoint Not Found")


def run_server(port: int = 8080):
    server_address = ("", port)
    httpd = http.server.ThreadingHTTPServer(server_address, GameHTTPRequestHandler)
    print(f"\n🚀 Guess the Number Web Server running at: http://localhost:{port}/")
    print(f"👉 Press Ctrl+C in this terminal to stop the server.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    run_server(8080)
