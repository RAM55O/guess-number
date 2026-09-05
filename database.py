"""SQLite Database Handler for Guess the Number Game."""

import sqlite3
import os
import contextlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from models import Player, GameRecord, GuessRecord, PlayerStats


class Database:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("DB_PATH", "game.db")
        parent_dir = os.path.dirname(self.db_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        self._init_db()

    @contextlib.contextmanager
    def _connection(self):
        """Context manager that ensures connection is properly committed and closed."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema with required tables and indexes."""
        with self._connection() as conn:
            cursor = conn.cursor()
            
            # Players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Games history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER NOT NULL,
                    difficulty TEXT NOT NULL,
                    target_number INTEGER NOT NULL,
                    attempts_used INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    is_won INTEGER NOT NULL,
                    score INTEGER NOT NULL,
                    duration_seconds REAL NOT NULL,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES players (id) ON DELETE CASCADE
                )
            """)

            # Detailed guess history per game
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    guess_number INTEGER NOT NULL,
                    hint_given TEXT NOT NULL,
                    guess_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE
                )
            """)

            # Indexes for fast lookup
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_player ON games(player_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_games_score ON games(score DESC);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_guesses_game ON guesses(game_id);")

    # --- Player Management ---

    def get_or_create_player(self, username: str) -> Player:
        """Fetch player by username or create a new one."""
        username = username.strip()
        if not username:
            username = "Player"

        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, created_at FROM players WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return Player(id=row["id"], username=row["username"], created_at=row["created_at"])
            
            cursor.execute("INSERT INTO players (username) VALUES (?)", (username,))
            player_id = cursor.lastrowid
            return Player(id=player_id, username=username, created_at=datetime.now())

    def get_all_players(self) -> List[Player]:
        """Get all registered players."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, created_at FROM players ORDER BY username ASC")
            return [Player(id=r["id"], username=r["username"], created_at=r["created_at"]) for r in cursor.fetchall()]

    # --- Game Operations ---

    def save_game(self, game: GameRecord) -> int:
        """Save a completed game record along with its guess log."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO games (
                    player_id, difficulty, target_number, attempts_used,
                    max_attempts, is_won, score, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                game.player_id,
                game.difficulty,
                game.target_number,
                game.attempts_used,
                game.max_attempts,
                1 if game.is_won else 0,
                game.score,
                game.duration_seconds
            ))
            game_id = cursor.lastrowid
            
            for guess in game.guesses:
                cursor.execute("""
                    INSERT INTO guesses (game_id, guess_number, hint_given)
                    VALUES (?, ?, ?)
                """, (game_id, guess.guess_number, guess.hint_given))

            return game_id

    def get_player_stats(self, player_id: int) -> Optional[PlayerStats]:
        """Get summarized statistics for a given player."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    p.username,
                    COUNT(g.id) as total_games,
                    SUM(CASE WHEN g.is_won = 1 THEN 1 ELSE 0 END) as games_won,
                    MAX(g.score) as high_score,
                    MIN(CASE WHEN g.is_won = 1 THEN g.attempts_used ELSE NULL END) as best_attempts,
                    SUM(g.score) as total_score
                FROM players p
                LEFT JOIN games g ON p.id = g.player_id
                WHERE p.id = ?
                GROUP BY p.id
            """, (player_id,))
            row = cursor.fetchone()
            if not row or row["total_games"] is None or row["total_games"] == 0:
                return None
            
            total_games = row["total_games"]
            games_won = row["games_won"] or 0
            win_rate = (games_won / total_games * 100) if total_games > 0 else 0.0

            return PlayerStats(
                username=row["username"],
                total_games=total_games,
                games_won=games_won,
                win_rate=round(win_rate, 1),
                high_score=row["high_score"] or 0,
                best_attempts=row["best_attempts"],
                total_score=row["total_score"] or 0
            )

    def get_player_games(self, player_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent games for a specific player."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, difficulty, target_number, attempts_used, max_attempts,
                       is_won, score, duration_seconds, played_at
                FROM games
                WHERE player_id = ?
                ORDER BY played_at DESC
                LIMIT ?
            """, (player_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_game_details(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve full details for a game including individual guesses."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT g.*, p.username
                FROM games g
                JOIN players p ON g.player_id = p.id
                WHERE g.id = ?
            """, (game_id,))
            game_row = cursor.fetchone()
            if not game_row:
                return None

            cursor.execute("""
                SELECT guess_number, hint_given, guess_time
                FROM guesses
                WHERE game_id = ?
                ORDER BY id ASC
            """, (game_id,))
            guesses = [dict(r) for r in cursor.fetchall()]

            result = dict(game_row)
            result["guesses"] = guesses
            return result

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get global top scores across all games."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    g.id as game_id,
                    p.username,
                    g.difficulty,
                    g.score,
                    g.attempts_used,
                    g.max_attempts,
                    g.duration_seconds,
                    g.played_at
                FROM games g
                JOIN players p ON g.player_id = p.id
                WHERE g.is_won = 1
                ORDER BY g.score DESC, g.duration_seconds ASC
                LIMIT ?
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_overall_stats(self) -> Dict[str, Any]:
        """Aggregate stats across all players and games."""
        with self._connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(id) as total_games_played,
                    SUM(CASE WHEN is_won = 1 THEN 1 ELSE 0 END) as total_games_won,
                    MAX(score) as highest_score,
                    AVG(duration_seconds) as avg_duration
                FROM games
            """)
            game_stats = dict(cursor.fetchone() or {})
            
            cursor.execute("SELECT COUNT(id) as total_players FROM players")
            player_count = cursor.fetchone()["total_players"]
            
            game_stats["total_players"] = player_count
            return game_stats
