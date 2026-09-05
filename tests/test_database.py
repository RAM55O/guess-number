"""Unit tests for SQLite database operations."""

import unittest
import os
import gc
from database import Database
from models import GameRecord, GuessRecord


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_db_path = f"test_game_{self._testMethodName}.db"
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)
        self.db = Database(self.temp_db_path)

    def tearDown(self):
        del self.db
        gc.collect()
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_create_and_get_player(self):
        player1 = self.db.get_or_create_player("Alice")
        self.assertIsNotNone(player1.id)
        self.assertEqual(player1.username, "Alice")

        # Same username should return same player ID (case-insensitive)
        player2 = self.db.get_or_create_player("alice")
        self.assertEqual(player1.id, player2.id)

    def test_save_game_and_guesses(self):
        player = self.db.get_or_create_player("Bob")
        game = GameRecord(
            player_id=player.id,
            difficulty="Medium",
            target_number=42,
            attempts_used=3,
            max_attempts=7,
            is_won=True,
            score=350,
            duration_seconds=15.2,
            guesses=[
                GuessRecord(guess_number=50, hint_given="Too HIGH"),
                GuessRecord(guess_number=25, hint_given="Too LOW"),
                GuessRecord(guess_number=42, hint_given="CORRECT")
            ]
        )
        game_id = self.db.save_game(game)
        self.assertGreater(game_id, 0)

        details = self.db.get_game_details(game_id)
        self.assertIsNotNone(details)
        self.assertEqual(details["target_number"], 42)
        self.assertEqual(details["is_won"], 1)
        self.assertEqual(len(details["guesses"]), 3)

    def test_player_stats_and_leaderboard(self):
        p1 = self.db.get_or_create_player("Champion")
        p2 = self.db.get_or_create_player("Novice")

        # p1 wins
        self.db.save_game(GameRecord(
            player_id=p1.id, difficulty="Hard", target_number=100, attempts_used=2,
            max_attempts=5, is_won=True, score=900, duration_seconds=10.0
        ))
        # p2 loses
        self.db.save_game(GameRecord(
            player_id=p2.id, difficulty="Easy", target_number=30, attempts_used=10,
            max_attempts=10, is_won=False, score=0, duration_seconds=40.0
        ))

        p1_stats = self.db.get_player_stats(p1.id)
        self.assertEqual(p1_stats.total_games, 1)
        self.assertEqual(p1_stats.games_won, 1)
        self.assertEqual(p1_stats.win_rate, 100.0)
        self.assertEqual(p1_stats.high_score, 900)

        p2_stats = self.db.get_player_stats(p2.id)
        self.assertEqual(p2_stats.total_games, 1)
        self.assertEqual(p2_stats.games_won, 0)
        self.assertEqual(p2_stats.win_rate, 0.0)

        leaderboard = self.db.get_leaderboard(limit=5)
        self.assertEqual(len(leaderboard), 1)
        self.assertEqual(leaderboard[0]["username"], "Champion")
        self.assertEqual(leaderboard[0]["score"], 900)


if __name__ == "__main__":
    unittest.main()
