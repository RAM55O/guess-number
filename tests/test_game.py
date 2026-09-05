"""Unit tests for Game Engine and Hint Generation."""

import unittest
from game_logic import GameEngine
from models import Difficulty, DifficultyConfig


class TestGameEngine(unittest.TestCase):
    def test_difficulty_boundaries(self):
        engine_easy = GameEngine(Difficulty.EASY)
        self.assertGreaterEqual(engine_easy.target_number, 1)
        self.assertLessEqual(engine_easy.target_number, 50)
        self.assertEqual(engine_easy.max_attempts, 10)

        engine_medium = GameEngine(Difficulty.MEDIUM)
        self.assertGreaterEqual(engine_medium.target_number, 1)
        self.assertLessEqual(engine_medium.target_number, 100)
        self.assertEqual(engine_medium.max_attempts, 7)

    def test_custom_difficulty(self):
        cfg = DifficultyConfig(min_val=50, max_val=60, max_attempts=4, base_points=200)
        engine = GameEngine(Difficulty.CUSTOM, custom_config=cfg)
        self.assertGreaterEqual(engine.target_number, 50)
        self.assertLessEqual(engine.target_number, 60)
        self.assertEqual(engine.max_attempts, 4)

    def test_correct_guess(self):
        engine = GameEngine(Difficulty.MEDIUM)
        target = engine.target_number
        is_correct, hint_msg, meta = engine.check_guess(target)

        self.assertTrue(is_correct)
        self.assertTrue(engine.is_game_over)
        self.assertTrue(engine.is_won)
        self.assertGreater(meta["score"], 0)
        self.assertEqual(engine.attempts_used, 1)

    def test_directional_hints_and_range_narrowing(self):
        engine = GameEngine(Difficulty.MEDIUM)
        engine.target_number = 50

        # Guess too low
        is_correct, hint, meta = engine.check_guess(20)
        self.assertFalse(is_correct)
        self.assertIn("Too LOW", hint)
        self.assertEqual(engine.current_low, 21)

        # Guess too high
        is_correct, hint, meta = engine.check_guess(80)
        self.assertFalse(is_correct)
        self.assertIn("Too HIGH", hint)
        self.assertEqual(engine.current_high, 79)

    def test_max_attempts_exhaustion(self):
        cfg = DifficultyConfig(min_val=1, max_val=10, max_attempts=2, base_points=100)
        engine = GameEngine(Difficulty.CUSTOM, custom_config=cfg)
        engine.target_number = 9

        engine.check_guess(1)
        self.assertFalse(engine.is_game_over)

        engine.check_guess(2)
        self.assertTrue(engine.is_game_over)
        self.assertFalse(engine.is_won)


if __name__ == "__main__":
    unittest.main()
