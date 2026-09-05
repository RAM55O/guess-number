"""Unified launcher for Guess the Number (CLI or Web UI).

Supports both interactive local execution and headless/containerized (Docker) environments.
"""

import argparse
import os
import sys
import webbrowser
from database import Database
from cli import CLIApp
from web_server import run_server

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


def is_interactive() -> bool:
    """Check if the current process is running in an interactive terminal."""
    return sys.stdin is not None and sys.stdin.isatty()


def open_browser_safe(url: str):
    """Safely attempt to open a browser without crashing in headless/Docker environments."""
    try:
        if is_interactive() and "DISPLAY" in os.environ or sys.platform in ("win32", "darwin"):
            webbrowser.open(url)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Guess the Number Game with SQLite Database")
    parser.add_argument("--cli", action="store_true", help="Launch interactive Terminal CLI mode")
    parser.add_argument("--web", action="store_true", help="Launch Modern Web Browser UI mode")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 8080)),
        help="Web server port (default: 8080 or $PORT env var)"
    )
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    
    args = parser.parse_args()
    port = args.port

    # Respect MODE environment variable (e.g., MODE=web or MODE=cli)
    env_mode = os.environ.get("MODE", "").lower()
    if env_mode == "web":
        args.web = True
    elif env_mode == "cli":
        args.cli = True

    if args.cli:
        db = Database("game.db")
        app = CLIApp(db)
        app.start()
        return

    if args.web:
        url = f"http://localhost:{port}/"
        if not args.no_browser:
            open_browser_safe(url)
        run_server(port)
        return

    # If running in a non-interactive environment (e.g. Docker daemon without stdin), default to Web Server
    if not is_interactive():
        print(f"[INFO] Non-interactive environment detected (Docker/Daemon).")
        print(f"[INFO] Starting Guess the Number Web Server on port {port}...")
        run_server(port)
        return

    # Interactive choice if running in a real interactive terminal
    print("==================================================")
    print("       🎲  GUESS THE NUMBER - PYTHON & SQLITE     ")
    print("==================================================")
    print("Select interface mode:")
    print("  [1] Interactive Terminal CLI")
    print(f"  [2] Web Browser Interface (http://localhost:{port})")
    print("  [3] Exit")
    print("==================================================")

    try:
        choice = input(f"Enter choice (1/2/3) [Default: 1]: ").strip()
    except (EOFError, KeyboardInterrupt):
        # Fallback if stdin suddenly closes
        print(f"\n[INFO] End of input detected. Starting Web Server on port {port}...")
        run_server(port)
        return

    if choice == "2":
        url = f"http://localhost:{port}/"
        if not args.no_browser:
            open_browser_safe(url)
        run_server(port)
    elif choice == "3":
        print("Goodbye!")
        sys.exit(0)
    else:
        db = Database("game.db")
        app = CLIApp(db)
        app.start()


if __name__ == "__main__":
    main()
