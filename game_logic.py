"""Core game logic, hint generator, and scoring system for Guess the Number."""

import random
import time
from typing import Tuple, Optional, List
from models import Difficulty, DifficultyConfig, DIFFICULTY_PRESETS, GameRecord, GuessRecord


class GameEngine:
    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM, custom_config: Optional[DifficultyConfig] = None):
        self.difficulty = difficulty
        if difficulty == Difficulty.CUSTOM and custom_config:
            self.config = custom_config
        else:
            self.config = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS[Difficulty.MEDIUM])

        self.min_bound = self.config.min_val
        self.max_bound = self.config.max_val
        self.current_low = self.min_bound
        self.current_high = self.max_bound
        
        self.target_number = random.randint(self.min_bound, self.max_bound)
        self.attempts_used = 0
        self.max_attempts = self.config.max_attempts
        self.guesses: List[GuessRecord] = []
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.is_game_over = False
        self.is_won = False

    def check_guess(self, guess: int) -> Tuple[bool, str, dict]:
        """
        Process a guess, generate hints, and update game state.
        
        Returns:
            Tuple of (is_correct, hint_message, extra_metadata)
        """
        if self.is_game_over:
            return False, "Game is already over.", {}

        self.attempts_used += 1
        
        # Exact match
        if guess == self.target_number:
            self.is_game_over = True
            self.is_won = True
            self.end_time = time.time()
            hint_msg = f"🎉 Correct! You found {self.target_number} in {self.attempts_used} attempt(s)!"
            self.guesses.append(GuessRecord(guess_number=guess, hint_given="CORRECT"))
            
            score = self.calculate_score()
            meta = {
                "attempts_used": self.attempts_used,
                "remaining_attempts": self.max_attempts - self.attempts_used,
                "score": score,
                "duration": round(self.end_time - self.start_time, 2),
                "is_won": True
            }
            return True, hint_msg, meta

        # Narrow range
        if guess < self.target_number:
            direction = "Too LOW! 📈 (Guess HIGHER)"
            if guess >= self.current_low:
                self.current_low = max(self.current_low, guess + 1)
        else:
            direction = "Too HIGH! 📉 (Guess LOWER)"
            if guess <= self.current_high:
                self.current_high = min(self.current_high, guess - 1)

        # Proximity hint
        diff = abs(guess - self.target_number)
        proximity = self._get_proximity_label(diff)

        # Build full hint
        hint_parts = [direction]
        if self.config.allow_proximity_hints:
            hint_parts.append(f"Temperature: {proximity}")

        hint_parts.append(f"Current Range: [{self.current_low} ... {self.current_high}]")

        # Bonus clue after several attempts
        bonus_clue = self._get_bonus_clue()
        if bonus_clue:
            hint_parts.append(f"💡 Bonus Clue: {bonus_clue}")

        hint_msg = " | ".join(hint_parts)
        self.guesses.append(GuessRecord(guess_number=guess, hint_given=hint_msg))

        # Check if attempts exhausted
        if self.attempts_used >= self.max_attempts:
            self.is_game_over = True
            self.is_won = False
            self.end_time = time.time()
            hint_msg += f"\n❌ Out of attempts! The target number was {self.target_number}."

        meta = {
            "attempts_used": self.attempts_used,
            "remaining_attempts": max(0, self.max_attempts - self.attempts_used),
            "range": (self.current_low, self.current_high),
            "is_game_over": self.is_game_over,
            "is_won": self.is_won,
            "target": self.target_number if self.is_game_over else None,
            "score": self.calculate_score() if self.is_won else 0
        }
        return False, hint_msg, meta

    def _get_proximity_label(self, diff: int) -> str:
        total_range = self.max_bound - self.min_bound + 1
        pct = diff / total_range

        if diff <= 2:
            return "🔥 ON FIRE!"
        elif pct <= 0.05:
            return "♨️ Boiling Hot"
        elif pct <= 0.15:
            return "☀️ Warm"
        elif pct <= 0.35:
            return "⛅ Cool"
        else:
            return "❄️ Freezing Cold"

    def _get_bonus_clue(self) -> Optional[str]:
        """Provides dynamic clues based on attempt counts."""
        if not self.config.allow_bonus_clues:
            return None

        if self.attempts_used == 3:
            parity = "EVEN" if self.target_number % 2 == 0 else "ODD"
            return f"The number is {parity}."
        elif self.attempts_used == 5:
            for d in [3, 5, 7]:
                if self.target_number % d == 0:
                    return f"The number is divisible by {d}."
            return f"The sum of digits is {sum(int(d) for d in str(self.target_number))}."
        elif self.attempts_used == 7:
            return f"The first digit is '{str(self.target_number)[0]}'."
        return None

    def calculate_score(self) -> int:
        """Calculate score based on difficulty base points, efficiency, and speed."""
        if not self.is_won:
            return 0
        
        duration = (self.end_time or time.time()) - self.start_time
        base_points = self.config.base_points
        
        # Remaining attempts bonus
        attempts_left = self.max_attempts - self.attempts_used
        attempt_multiplier = 1.0 + (attempts_left / self.max_attempts)
        
        # Time bonus (up to 20% extra if under 30 seconds)
        time_bonus = max(0, 1.0 - (duration / 60.0)) * 0.2
        
        final_score = int(base_points * attempt_multiplier * (1.0 + time_bonus))
        return final_score

    def to_game_record(self, player_id: int) -> GameRecord:
        """Convert game state into a persistable GameRecord."""
        duration = (self.end_time or time.time()) - self.start_time
        return GameRecord(
            player_id=player_id,
            difficulty=self.difficulty.value,
            target_number=self.target_number,
            attempts_used=self.attempts_used,
            max_attempts=self.max_attempts,
            is_won=self.is_won,
            score=self.calculate_score(),
            duration_seconds=round(duration, 2),
            guesses=self.guesses
        )
