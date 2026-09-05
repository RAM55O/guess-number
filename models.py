"""Data models and configuration for the Guess the Number game."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    CUSTOM = "Custom"

    @classmethod
    def from_string(cls, name: str) -> "Difficulty":
        for member in cls:
            if member.value.lower() == name.lower():
                return member
        return cls.MEDIUM


@dataclass
class DifficultyConfig:
    min_val: int
    max_val: int
    max_attempts: int
    base_points: int
    allow_proximity_hints: bool = True
    allow_bonus_clues: bool = True


DIFFICULTY_PRESETS = {
    Difficulty.EASY: DifficultyConfig(min_val=1, max_val=50, max_attempts=10, base_points=100),
    Difficulty.MEDIUM: DifficultyConfig(min_val=1, max_val=100, max_attempts=7, base_points=250),
    Difficulty.HARD: DifficultyConfig(min_val=1, max_val=500, max_attempts=5, base_points=500),
}


@dataclass
class Player:
    id: Optional[int] = None
    username: str = ""
    created_at: Optional[datetime] = None


@dataclass
class GuessRecord:
    id: Optional[int] = None
    game_id: Optional[int] = None
    guess_number: int = 0
    hint_given: str = ""
    guess_time: Optional[datetime] = None


@dataclass
class GameRecord:
    id: Optional[int] = None
    player_id: Optional[int] = None
    username: Optional[str] = None
    difficulty: str = Difficulty.MEDIUM.value
    target_number: int = 0
    attempts_used: int = 0
    max_attempts: int = 0
    is_won: bool = False
    score: int = 0
    duration_seconds: float = 0.0
    played_at: Optional[datetime] = None
    guesses: List[GuessRecord] = field(default_factory=list)


@dataclass
class PlayerStats:
    username: str
    total_games: int
    games_won: int
    win_rate: float
    high_score: int
    best_attempts: Optional[int]
    total_score: int
